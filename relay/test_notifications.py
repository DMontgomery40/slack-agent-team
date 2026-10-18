import json,unittest
import routing
from notifications import Store,parse_result
from relay_testlib import LabCase,lab,event,BOT,HUMAN,STRANGER

class PolicyTests(LabCase):
    def plan(self,e,prefs=None):return routing.plan(self.cfg,e,prefs or {})

    def test_duplicate_identical_runtime_envelope_is_not_a_second_turn(self):
        raw='{"receipt":"abc","reply":null,"memory":"blue"}'
        self.assertEqual(parse_result(raw+raw,'abc')['memory'],'blue')
        with self.assertRaises(ValueError):parse_result(raw+'{"receipt":"abc","reply":"conflict"}','abc')

    def test_untagged_update_reaches_followers_silently(self):
        p=self.plan(event())
        self.assertEqual(set(p),set(self.cfg.bots))
        self.assertFalse(any(v['reply'] for v in p.values()))

    def test_named_question_one_reply_peer_context_no_reply(self):
        p=self.plan(event(text='Antigravity, what review evidence is needed?'))
        self.assertEqual([n for n,v in p.items() if v['reply']],['antigravity'])
        # A teammate's @-mention asks for help: the mentioned seat may answer, without authority to change scope.
        p=self.plan(event(text=f'<@{BOT["grok"]}> do more work',user=BOT['cursor']))
        self.assertEqual([n for n,v in p.items() if v['reply']],['grok'])
        self.assertFalse(any(v['authority'] for v in p.values()))

    def test_lead_bot_posts_carry_authority_but_never_trigger_replies(self):
        p=self.plan(event(text='Grok, review this?',user=BOT['claude']))
        self.assertNotIn('claude',p)
        self.assertTrue(all(v['authority'] for v in p.values()))
        self.assertFalse(any(v['reply'] for v in p.values()))

    def test_preferences_mentions_mute_and_assignment(self):
        prefs={'grok':{'mode':'muted'},'cursor':{'mode':'mentions_only'},'muse':{'mode':'follow_assigned','topics':['packet']}}
        p=self.plan(event(text=f'<@{BOT["grok"]}> packet update'),prefs)
        self.assertNotIn('grok',p);self.assertNotIn('cursor',p);self.assertIn('muse',p)
        p=self.plan(event(text=f'<@{BOT["cursor"]}> help?'),prefs)
        self.assertTrue(p['cursor']['reply'])
        p=self.plan(event(text='Cursor, please assess this design.'),prefs)
        self.assertIn('cursor',p)

    def test_owned_topic_question_gets_owner_attention_instead_of_lead(self):
        p=self.plan(event(text='What evidence is needed for PKT-19?'),{'muse':{'mode':'follow_assigned','topics':['PKT-19']}})
        self.assertEqual([n for n,v in p.items() if v['reply']],['muse'])

    def test_reject_project_unknown_sender_thread_and_system_events(self):
        for patch in [{'team':'other'},{'channel':'other'},{'user':'stranger'},{'user':STRANGER},{'thread_ts':'0.01'},{'subtype':'message_changed'},{'subtype':'thread_broadcast','thread_ts':'0.5'}]:
            e=event();e.update(patch);self.assertEqual(self.plan(e),{},patch)

    def test_reviewer_tool_boundary(self):
        self.assertEqual(routing.client_response({'id':1,'method':'session/request_permission'})['result']['outcome']['outcome'],'cancelled')

class DurableTests(LabCase):
    def setUp(self):
        super().setUp();self.path=self.dir/'deliveries.sqlite';self.s=Store(self.path,self.cfg)

    def test_duplicate_restart_and_independent_busy_seats(self):
        self.s.ingest([event()])
        b=self.s.claim('grok');self.assertIsNotNone(b)
        self.assertIsNone(self.s.claim('grok'))
        self.assertIsNotNone(self.s.claim('muse'))
        self.s.ingest([event()])
        self.assertEqual(len(self.s.rows('grok')),1)
        t=Store(self.path,self.cfg);t.recover()
        self.assertEqual(t.rows('grok')[0]['status'],'ambiguous')
        self.assertIsNone(t.claim('grok'))
        self.assertIsNotNone(t.claim('cursor'))

    def test_mute_stops_queued_turns_unmute_catches_up_silently(self):
        self.s.ingest([event(text=f'<@{BOT["grok"]}> answer?')])
        self.s.preference('grok','muted')
        self.assertIsNone(self.s.claim('grok'))
        self.s.ingest([event('2.001')])
        self.s.preference('grok','follow_conversation')
        b=self.s.claim('grok');self.assertEqual(len(b['events']),2)
        self.assertFalse(any(e['reply'] for e in b['events']))

    def test_failure_holds_one_recipient_and_preserves_later_requests(self):
        self.s.ingest([event()]);b=self.s.claim('grok')
        self.s.fail(b['id'],'provider failed')
        self.s.ingest([event('2.001',text='Grok, assess this?')])
        self.assertIsNone(self.s.claim('grok'))
        self.assertEqual(self.s.rows('grok')[-1]['status'],'queued')
        self.assertIsNotNone(self.s.claim('cursor'))

    def test_resolve_releases_held_batch_without_replaying_it(self):
        self.s.ingest([event()]);b=self.s.claim('grok');self.s.fail(b['id'],'provider failed')
        self.s.ingest([event('2.001',text='Grok, assess this?')])
        self.s.resolve(b['id'])
        n=self.s.claim('grok');self.assertEqual([e['ts'] for e in n['events']],['2.001'])
        with self.assertRaises(ValueError):self.s.resolve(n['id'])

    def test_receipt_requires_actual_runtime_result_and_forced_silence(self):
        self.s.ingest([event()]);b=self.s.claim('muse')
        self.assertEqual(self.s.rows('muse')[0]['status'],'processing')
        with self.assertRaises(ValueError):parse_result('{"receipt":"wrong","reply":null}',b['id'])
        data=parse_result(json.dumps({'receipt':b['id'],'reply':'Noted','memory':'packet is blue'}),b['id'])
        self.s.complete(b,data)
        self.assertEqual(self.s.rows('muse')[0]['status'],'processed')
        self.assertEqual(self.s.batch(b['id'])['public_reply'],'')

    def test_gated_queue_and_question_boundary(self):
        self.s.ingest([event(),event('2.001',text='Muse, what color?'),event('3.001')])
        self.assertIsNone(self.s.claim('claude',gated=True))
        self.assertEqual(self.s.rows('claude')[0]['status'],'gated')
        b=self.s.claim('muse');self.assertEqual(len(b['events']),2)
        self.assertTrue(b['events'][-1]['reply'])
        self.assertIsNotNone(self.s.claim('claude',gated=False))

    def test_old_duplicate_does_not_move_intake_cursor_backwards(self):
        self.s.ingest([event('4.001')])
        self.s.ingest([event('1.001')])
        self.assertEqual(self.s.cursor('0'),'4.001')

    def test_context_only_seat_follows_preferences_and_never_replies(self):
        cfg=lab(self.dir,codex={'provider':'none'});s=Store(self.dir/'ctx.sqlite',cfg)
        self.assertNotIn('codex',cfg.workers())
        s.preference('codex','muted');s.ingest([event()])
        self.assertIsNone(s.claim('codex'))
        s.preference('codex','follow_conversation')
        s.ingest([event('2.001',text='Codex, can you check the tests?')])
        b=s.claim('codex');self.assertIsNotNone(b)
        self.assertFalse(any(e['reply'] for e in b['events']))
        s.complete(b,{'receipt':b['id'],'reply':'forged public text'})
        self.assertEqual(s.batch(b['id'])['public_reply'],'')

    def test_narrowing_preserves_matching_queued_context(self):
        self.s.ingest([event(text='Packet PKT-7 is available.')])
        self.s.preference('codex','follow_assigned',topics=['PKT-7'])
        self.assertIsNotNone(self.s.claim('codex'))
        self.s.ingest([event('2.001',text='Unrelated note.')])
        self.s.preference('grok','follow_assigned',topics=['PKT-7'])
        self.assertEqual([r['status'] for r in self.s.rows('grok')],['queued','skipped'])

if __name__=='__main__':unittest.main()
