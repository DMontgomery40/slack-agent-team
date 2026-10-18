"""Reply policy: untagged->lead, plain names, everyone, peers silent, top-level only, context revision."""
import json,os,time,unittest
import routing
from service import Slack,process_one,starting_watermark,health
from lead_ledger import record,lead_post,ledger_ts
from notifications import prompt
from team_context import read_context
from instance import Instance
from relay_testlib import LabCase,lab,load_example,event,bid_of,rev_of,BOT,CHANNEL,TEAM,HUMAN,OTHER_CHANNEL

def replies(cfg,text,prefs=None,user=None):
    p=routing.plan(cfg,event(text=text,**({'user':user} if user else {})),prefs or {})
    return {n for n,v in p.items() if v['reply']}

class ReplyPolicyTests(LabCase):
    def test_untagged_human_request_goes_to_lead_only(self):
        for text in ['What should we work on next?','Can you check the relay health','please summarize the plan','thoughts on the README']:
            self.assertEqual(replies(self.cfg,text),{'claude'},text)
    def test_plain_app_names_route_to_that_seat_longest_name_wins(self):
        cases={'Grok in Cursor, what do you think?':{'grok'},'Cursor Composer, review this?':{'cursor'},'Claude Code, status?':{'claude'},
            'Muse Code, thoughts?':{'muse'},'Codex, can you check the tests?':{'codex'},'Antigravity, review the diff?':{'antigravity'},
            'Grok and Codex, compare approaches?':{'grok','codex'},'Is cursor-agent slow today?':{'claude'},
            'Grok, what did Codex say about the plan?':{'grok'},'Grok, ask Claude about it?':{'grok'},'Hey Muse, can Cursor Composer help?':{'muse'},
            'Can Grok review this?':{'grok'}}
        for text,expected in cases.items():self.assertEqual(replies(self.cfg,text),expected,text)
    def test_everyone_addressed_request_lets_every_unmuted_seat_reply(self):
        for text in ['<!channel> what do you all think?','<!here|here> thoughts?','Everyone, what is next?','all of you: please review the plan',"y'all, any concerns?",'yall ready?','<!everyone> can you each confirm your model?']:
            self.assertEqual(replies(self.cfg,text),set(self.cfg.bots),text)
        self.assertEqual(replies(self.cfg,'Everyone, what is next?',{'grok':{'mode':'muted'},'cursor':{'mode':'mentions_only'}}),set(self.cfg.bots)-{'grok'})
        self.assertEqual(replies(self.cfg,'<!channel> deploy is at five.'),set())
    def test_incidental_group_words_do_not_broadcast(self):
        # Live bug: "a default for everyone" inside a seat's assignment addressed all five seats.
        cases={'Antigravity, please review the patch for any choice written as a default for everyone.':{'antigravity'},
            'Codex, can you tell all of you-know-who the plan?':{'codex'},
            'Is this good for y\'all to read later, Grok in Cursor?':{'grok'},
            'Please check whether the team rules apply to everyone?':{'claude'}}
        for text,expected in cases.items():self.assertEqual(replies(self.cfg,text),expected,text)
    def test_peer_and_bot_posts_never_trigger_public_replies(self):
        for user in BOT.values():
            for text in ['Everyone, what is next?','Grok, review this?','What should we do?',f'<@{BOT["cursor"]}> help?']:
                self.assertEqual(replies(self.cfg,text,user=user),set(),(user,text))
    def test_everyone_request_gets_exactly_one_reply_per_seat_end_to_end(self):
        s=self.store();s.ingest([event(text='Everyone, what is your model?')]);posts=[]
        def provider(name,p):
            if name=='antigravity':return f'BKRV1 {bid_of(p)}\nMEMORY\nAsked for models.\nREPLY TEXT\nantigravity here\nEND {bid_of(p)}'
            return json.dumps({'receipt':bid_of(p),'reply':f'{name} here','context_revision':rev_of(p)})
        for _ in range(2):
            for seat in self.cfg.workers():process_one(s,seat,provider,lambda text,key:posts.append(text) or str(len(posts)))
            s.ingest([event(text='Everyone, what is your model?')])
        self.assertEqual(sorted(posts),sorted(f'{n} here' for n in self.cfg.workers()))
    def test_untagged_request_end_to_end_posts_once_from_lead(self):
        s=self.store();s.ingest([event(text='What should we work on next?')]);posts=[]
        def provider(name,p):
            if name=='antigravity':return f'BKRV1 {bid_of(p)}\nMEMORY\nContext.\nREPLY NONE\nEND {bid_of(p)}'
            return json.dumps({'receipt':bid_of(p),'reply':f'{name} answer'})
        for seat in self.cfg.workers():process_one(s,seat,provider,lambda text,key:posts.append(text) or '9.1')
        self.assertEqual(posts,['claude answer'])
        self.assertFalse(any(b['status']=='failed' for b in s.status()['blocked']))

    def test_heard_reaction_marks_addressed_messages_only(self):
        # Live gap: a thanks post naming seats got no visible receipt. Addressed seats react; others stay quiet.
        s=self.store();s.ingest([event(ts='3.001',text='Muse Code: thanks, great review.'),event(ts='3.002',text='FYI the build is green.')])
        reacted={}
        def provider(name,p):
            if name=='antigravity':return f'BKRV1 {bid_of(p)}\nMEMORY\nContext.\nREPLY NONE\nEND {bid_of(p)}'
            return json.dumps({'receipt':bid_of(p),'reply':None})
        for seat in self.cfg.workers():
            while process_one(s,seat,provider,lambda text,key:'9.9',react=lambda ts,seat=seat:reacted.setdefault(seat,[]).append(ts)):pass
        self.assertEqual(reacted,{'muse':['3.001']})
    def test_heard_reaction_failure_never_blocks_the_turn(self):
        s=self.store();s.ingest([event(text='Codex, what changed?')]);posts=[]
        def boom(ts):raise RuntimeError('Slack API returned missing_scope')
        process_one(s,'codex',lambda n,p:json.dumps({'receipt':bid_of(p),'reply':'ACK: two files changed','context_revision':rev_of(p)}),lambda text,key:posts.append(text) or '9.2',react=boom)
        self.assertEqual(posts,['ACK: two files changed'])
    def test_prompt_carries_team_vocabulary(self):
        s=self.store();s.ingest([event(text='Codex, what changed?')]);seen=[]
        process_one(s,'codex',lambda n,p:seen.append(p) or json.dumps({'receipt':bid_of(p),'reply':None,'context_revision':rev_of(p)}),lambda *a:'9.3')
        for word in ['ACK','CLAIM','READY','PASS or FAIL','HOLD','BLOCKED','HANDOFF','ETA','never post a bare ACK']:self.assertIn(word,seen[0],word)

class InteractiveLeadTests(LabCase):
    """Ledgered lead posts are the interactive lead: they assign work like a trusted human. Unledgered lead-bot posts are context."""
    def setUp(self):
        super().setUp()
        for ts in ('6.5','6.6','6.001','7.001','8.001','10.001'):record(self.cfg,ts,'test')
    def test_unledgered_lead_bot_post_is_context_and_flagged(self):
        s=self.store();s.ingest([event('12.5',text=f'<@{BOT["codex"]}> please check the tests',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'12.5'),set());self.assertEqual(self.origin(s,'12.5'),'anomaly')
        self.assertEqual(health(self.cfg,s,[],None,None)['lead_identity_anomaly'],{'count':1,'recent':['12.5']})
    def test_ledger_wins_over_an_unconfirmed_relay_post(self):
        s=self.store();s.ingest([event('0.5',text='Claude, status?')]);b=s.claim('claude');s.complete(b,{'receipt':b['id'],'reply':'Green.'})
        s.ingest([event('6.001',text=f'<@{BOT["codex"]}> please check the tests',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'6.001'),{'codex'})
    def test_lead_post_ledgers_the_ts_privately(self):
        class FakePost:
            def post(self,text,key):return '20.001'
        self.assertEqual(lead_post(self.cfg,'Codex, check the tests?',slack=FakePost()),'20.001')
        self.assertIn('20.001',ledger_ts(self.cfg));self.assertEqual(self.cfg.lead_ledger.stat().st_mode&0o777,0o600)
        s=self.store();s.ingest([event('20.001',text='Codex, check the tests?',user=BOT['claude'])])
        self.assertEqual((self.origin(s,'20.001'),self.seat_replies(s,'20.001')),('interactive',{'codex'}))
    def seat_replies(self,s,ts):return {n for n in self.cfg.bots for r in s.rows(n) if r['ts']==ts and r['can_reply']}
    def origin(self,s,ts):
        with s.db() as db:return json.loads(db.execute('SELECT event FROM notification_events WHERE ts=?',(ts,)).fetchone()[0]).get('lead_origin')
    def test_interactive_lead_mention_gets_that_seat_to_reply(self):
        s=self.store();s.ingest([event('6.001',text=f'<@{BOT["codex"]}> please check the tests',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'6.001'),{'codex'});self.assertEqual(self.origin(s,'6.001'),'interactive')
        s.ingest([event('7.001',text='Grok in Cursor, review the plan?',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'7.001'),{'grok'})
    def test_lead_must_address_explicitly_roster_mentions_do_not_reply(self):
        s=self.store();s.ingest([event('6.5',text='Codex finished; is Grok next?',user=BOT['claude']),event('6.6',text='Grok and Codex, compare approaches?',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'6.5'),set());self.assertEqual(self.seat_replies(s,'6.6'),{'grok','codex'})
        self.assertEqual(replies(self.cfg,'Codex finished; is Grok next?'),{'codex'})  # humans keep the first-name fallback
    def test_multi_line_lead_assignment_gives_each_addressed_seat_one_reply(self):
        text=('Assignments for the skill review (REVIEW.patch is in each work dir):\n- Antigravity: review REVIEW.patch for correctness.\n'
            '- *Muse Code*: check the wording.\n- Codex: run the tests.\n2. Grok in Cursor: give a second review.\n- Cursor Composer, please check the links.')
        record(self.cfg,'30.001','test');s=self.store();s.ingest([event('30.001',text=text,user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'30.001'),{'antigravity','muse','codex','grok','cursor'})
        record(self.cfg,'31.001','test');s.ingest([event('31.001',text='Roster:\n- Codex: Model A, coding agent\n- Muse Code: Model B',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'31.001'),set())
        s.ingest([event('32.001',text='- Codex: run the tests.',user=BOT['grok'])])
        self.assertEqual(self.seat_replies(s,'32.001'),set())
    def test_seat_answered_elsewhere_gets_context_only(self):
        s=self.store();s.mark_answered('codex','6.001','6.9')
        s.ingest([event('6.001',text='Codex and Grok, please check the tests.',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'6.001'),{'grok'})
        b=s.claim('codex');self.assertEqual([(e['ts'],e['reply']) for e in b['events']],[('6.001',False)])
        s.ingest([event('7.001',text='Grok in Cursor, review the plan?',user=BOT['claude'])]);s.mark_answered('grok','7.001')
        self.assertEqual(self.seat_replies(s,'7.001'),set())
        with self.assertRaises(ValueError):s.mark_answered('codex','6.001')
    def test_relay_posted_claude_message_never_triggers_replies(self):
        s=self.store();s.ingest([event('0.5',text='Claude, status?')]);b=s.claim('claude');s.complete(b,{'receipt':b['id'],'reply':'Status is green.'});s.posted(b,'5.000')
        s.ingest([event('5.000',text=f'<@{BOT["codex"]}> please check the tests',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'5.000'),set());self.assertEqual(self.origin(s,'5.000'),'relay')
    def test_unconfirmed_relay_post_fails_closed(self):
        s=self.store();s.ingest([event('0.5',text='Claude, status?')]);b=s.claim('claude');s.complete(b,{'receipt':b['id'],'reply':'Green.'})
        s.ingest([event('5.000',text=f'<@{BOT["codex"]}> check?',user=BOT['claude'])])
        self.assertEqual(self.seat_replies(s,'5.000'),set());self.assertEqual(self.origin(s,'5.000'),'uncertain')
        self.assertTrue(health(self.cfg,s,[],None,None)['leadOriginUncertain'])
    def test_untagged_lead_request_is_context_only_and_spoofed_origin_ignored(self):
        s=self.store();s.ingest([event('8.001',text='What should we do next?',user=BOT['claude']),event('9.001',text='Codex, check?',user=BOT['grok'],lead_origin='interactive')])
        self.assertEqual(self.seat_replies(s,'8.001'),set());self.assertEqual(self.seat_replies(s,'9.001'),set())
    def test_lead_everyone_request_gets_one_reply_per_seat_and_no_chain(self):
        s=self.store();s.ingest([event('10.001',text='Everyone, please post your model.',user=BOT['claude'])]);posts=[]
        def provider(name,p):
            if name=='antigravity':return f'BKRV1 {bid_of(p)}\nMEMORY\nModel asked.\nREPLY TEXT\nantigravity model\nEND {bid_of(p)}'
            return json.dumps({'receipt':bid_of(p),'reply':f'{name} model'})
        def post(name):
            def send(text,key):
                ts=f'{11+len(posts)}.001';posts.append((name,ts));return ts
            return send
        for _ in range(3):
            for seat in self.cfg.workers():process_one(s,seat,provider,post(seat))
            # Seat replies come back through history as bot posts: context only, never a new request.
            s.ingest([event(ts,text=f'{n} model. Everyone, thoughts?',user=BOT[n]) for n,ts in posts])
        self.assertEqual(sorted(n for n,_ in posts),sorted(set(self.cfg.workers())-{'claude'}))

class FakeSlack:
    def __init__(self,user):self.user=user;self.calls=[]
    def __call__(self,method,data,token):
        self.calls.append((method,dict(data)))
        if method=='auth.test':return {'ok':True,'team_id':TEAM,'user_id':self.user}
        return {'ok':True,'ts':'5.5','messages':[]}

class SlackGuardTests(LabCase):
    def setUp(self):
        super().setUp()
        self.cfg.credentials_dir=self.dir
        for seat in self.cfg.seats:
            p=self.dir/f'slack-{seat}.env';p.write_text('SLACK_BOT_TOKEN=xoxb-test-only\n');p.chmod(0o600)
    def test_posts_are_top_level_in_instance_channel_only(self):
        t=FakeSlack(BOT['grok']);s=Slack(self.cfg,'grok',t)
        self.assertEqual(s.post('hello','k1'),'5.5')
        method,data=t.calls[-1]
        self.assertEqual((method,data['channel']),('chat.postMessage',CHANNEL));self.assertNotIn('thread_ts',data);self.assertNotIn('reply_broadcast',data)
        for bad in [{'thread_ts':'1.0'},{'reply_broadcast':True}]:
            with self.assertRaises(RuntimeError):s.call('chat.postMessage',dict({'channel':CHANNEL,'text':'x'},**bad))
        with self.assertRaises(RuntimeError):s.call('chat.postMessage',{'text':'no channel'})
        self.assertEqual(len(t.calls),2)
    def test_wrong_channel_is_rejected_before_any_request(self):
        t=FakeSlack(BOT['claude']);s=Slack(self.cfg,'claude',t)
        for method in ['conversations.history','chat.postMessage','conversations.replies']:
            with self.assertRaises(RuntimeError):s.call(method,{'channel':OTHER_CHANNEL})
        self.assertEqual([m for m,_ in t.calls],['auth.test'])
        self.assertEqual(routing.plan(self.cfg,event(channel=OTHER_CHANNEL,text='Grok?'),{}),{})
    def test_identity_and_credential_privacy_checked(self):
        with self.assertRaisesRegex(RuntimeError,'identity'):Slack(self.cfg,'grok',FakeSlack(BOT['cursor']))
        (self.dir/'slack-muse.env').chmod(0o644)
        with self.assertRaisesRegex(RuntimeError,'private'):Slack(self.cfg,'muse',FakeSlack(BOT['muse']))

class ContextAndIdentityTests(LabCase):
    def test_context_text_and_revision_reach_prompt_and_receipt(self):
        (self.dir/'TEAM_CONTEXT.md').write_text('Lab decision: alpha wins.\n')
        rev=read_context(self.cfg)['revision'];s=self.store();s.ingest([event(text='Grok, which option won?')]);seen=[]
        def provider(name,p):seen.append(p);return json.dumps({'receipt':bid_of(p),'reply':'Alpha.','context_revision':rev})
        process_one(s,'grok',provider,lambda text,key:'7.1')
        self.assertIn('Lab decision: alpha wins.',seen[0]);self.assertEqual(rev_of(seen[0]),rev)
        b=s.batch(s.rows('grok')[0]['batch'])
        self.assertEqual((b['status'],b['context_rev'],b['echoed_rev']),('replied',rev,rev))
        (self.dir/'TEAM_CONTEXT.md').write_text('Lab decision: beta wins.\n')
        self.assertNotEqual(read_context(self.cfg)['revision'],rev)
    def test_stale_echo_is_held_missing_echo_is_tolerated(self):
        s=self.store();s.ingest([event(text='Grok, status?'),event('2.001',text='Cursor, status?')])
        process_one(s,'grok',lambda n,p:json.dumps({'receipt':bid_of(p),'reply':'x','context_revision':'sha256:0000000000000000'}),lambda *a:self.fail('stale turn must not post'))
        self.assertEqual(s.rows('grok')[0]['status'],'failed')
        process_one(s,'cursor',lambda n,p:json.dumps({'receipt':bid_of(p),'reply':'ok then'}),lambda *a:'8.1')
        self.assertEqual(s.rows('cursor')[-1]['status'],'replied')
    def test_every_prompt_states_exact_identity_project_lead_and_no_threads(self):
        ctx=read_context(self.cfg);self.assertFalse(ctx['present'])
        for seat,s in self.cfg.seats.items():
            p=prompt(self.cfg,{'id':'B','name':seat,'events':[]},ctx)
            lead=self.cfg.seats[self.cfg.lead]
            for fragment in [f"You are {s['app_name']} (seat {seat}",f"one member of {self.cfg.owner}'s agent team",self.cfg.project['name'],f"It is NOT {self.cfg.project['not']}",
                    f"{lead['app_name']} {lead['model_label']} leads",'no threads','top-level',ctx['revision']]:
                self.assertIn(fragment,p,(seat,fragment))
            self.assertNotIn('REVIEW ONLY',p);self.assertEqual('headless' in p,seat=='claude')
            self.assertIn("own harness settings",p);self.assertNotIn('Never take external actions',p);self.assertIn(str(self.cfg.seat_cwd(seat)),p);self.assertNotIn('Use no tools',p)
        self.assertIn('Grok in Cursor is seat grok',p);self.assertIn('Cursor Composer is seat cursor',p)
    def test_prompt_owner_and_project_come_from_config(self):
        data=json.loads(json.dumps(self.cfg.data));data.pop('owner');data['trusted_humans']={HUMAN:'Robin'}
        data['project']={'name':'widget repo','description':'Widgets.'}
        cfg=Instance(data,self.dir);self.assertEqual(cfg.owner,'Robin')
        p=prompt(cfg,{'id':'B','name':'codex','events':[]},read_context(cfg))
        for fragment in ["one member of Robin's agent team",'This channel is the widget repo: Widgets.','Trusted humans: Robin']:self.assertIn(fragment,p)
        self.assertNotIn('It is NOT',p)
        data['owner']='Team Lead';self.assertIn("Team Lead's agent team",prompt(Instance(data,self.dir),{'id':'B','name':'codex','events':[]},read_context(cfg)))

class RoleAndPostureTests(LabCase):
    def test_unaddressed_review_request_goes_to_lead_not_antigravity(self):
        for text in ['Can someone review this diff?','Please review the README changes.','review the plan?']:
            self.assertEqual(replies(self.cfg,text),{'claude'},text)
    def test_role_policy_is_opt_in_only(self):
        self.assertFalse(any(s.get('role_policy') for s in self.cfg.seats.values()))
        cfg=lab(self.dir,antigravity={'role_policy':'review-only'})
        self.assertIn('REVIEW ONLY',prompt(cfg,{'id':'B','name':'antigravity','events':[]},read_context(cfg)))
        self.assertEqual(replies(cfg,'Can someone review this diff?'),{'claude'})
    def test_every_seat_defaults_to_harness_tools_in_its_own_scratch_clone(self):
        cfg=load_example(self.dir)
        for seat in cfg.workers():
            self.assertEqual(cfg.tools(seat),'harness-default')
            self.assertEqual(cfg.seat_cwd(seat),cfg.dir/'work'/seat)
            self.assertNotEqual(cfg.seat_cwd(seat).resolve(),cfg.source_repo.resolve())
        self.assertEqual(cfg.seats['antigravity'].get('acp_permission'),'deny')
        with self.assertRaises(ValueError):lab(self.dir,grok={'cwd':str(cfg.source_repo)})
    def test_token_shaped_text_is_redacted_from_public_replies(self):
        s=self.store();s.ingest([event(text='Grok, what is in the env file?')]);posts=[]
        process_one(s,'grok',lambda n,p:json.dumps({'receipt':bid_of(p),'reply':'It holds '+'xoxb-'+'1234567890-abcdefghij'}),lambda text,key:posts.append(text) or '1.2')
        self.assertEqual(posts,['It holds [REDACTED]'])
    def test_provider_usage_is_recorded_on_the_batch(self):
        s=self.store();s.ingest([event(text='Grok, status?')])
        process_one(s,'grok',lambda n,p:{'text':json.dumps({'receipt':bid_of(p),'reply':'Fine.'}),'usage':{'usage':{'inputTokens':12}}},lambda *a:'4.4')
        b=s.batch(s.rows('grok')[0]['batch'])
        self.assertEqual((b['status'],json.loads(b['usage'])),('replied',{'usage':{'inputTokens':12}}))

class LifecycleTests(LabCase):
    def test_first_start_watermark_is_now_by_default_and_stable(self):
        self.cfg.data['slack'].pop('initial_watermark',None)
        before=time.time();ts=starting_watermark(self.cfg)
        self.assertGreaterEqual(float(ts),before-1);self.assertEqual(starting_watermark(self.cfg),ts)
    def test_configured_initial_watermark_is_used_on_first_start(self):
        self.assertIsNone(self.cfg.data['slack']['initial_watermark'],'the example must not replay channel backlog')
        configured='1700000000.000100';self.cfg.data['slack']['initial_watermark']=configured
        self.assertEqual(starting_watermark(self.cfg),configured)
    def test_health_reports_thread_intake_unsupported(self):
        h=health(self.cfg,self.store(),[],None,'RuntimeError: Slack API returned missing_scope')
        self.assertFalse(h['threadIntake']);self.assertIn('unsupported',h['threadReplies']);self.assertEqual(h['channel'],CHANNEL)
        self.assertEqual(h['contextRevision'],read_context(self.cfg)['revision'])
    def test_example_config_loads_with_six_worker_seats(self):
        cfg=load_example(self.dir)
        self.assertEqual((cfg.team,cfg.channel,cfg.lead,cfg.poll_seat),('T00000000','C00000000','claude','claude'))
        self.assertEqual(set(cfg.workers()),{'claude','codex','muse','grok','cursor','antigravity'})
        self.assertEqual(set(cfg.trusted),{'U0000000001'})
        self.assertEqual(health(cfg,self.store(),[],None,None)['posture']['antigravity'],{'posture':'inherit','tools':'harness-default','cwd':str(cfg.dir/'work'/'antigravity'),'role_policy':None})
        h=health(cfg,self.store(),[],None,None)
        self.assertIn('anything an agent can do interactively',h['postureWarning']);self.assertTrue(any('/tmp' in x for x in h['knownLimits']))
        locked=lab(self.dir,claude={'posture':'locked'})
        self.assertIn('Never take external actions',prompt(locked,{'id':'B','name':'claude','events':[]},read_context(locked)))

if __name__=='__main__':unittest.main()
