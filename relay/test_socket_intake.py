"""Socket Mode push intake with polling as reconciliation, plus the ingest-time heard reaction. Fakes only; no live socket."""
import importlib.util,json,threading,time,unittest
from types import SimpleNamespace
from unittest import mock
import socket_intake
from socket_intake import Intake,Heard
from service import poll_once,health
from lead_ledger import ingest_lock
from relay_testlib import LabCase,TEAM,CHANNEL,HUMAN,BOT,OTHER_CHANNEL

def payload(ts,text='Hello team.',user=HUMAN,channel=CHANNEL,event_id=None,**extra):
    event=dict({'type':'message','channel':channel,'user':user,'text':text,'ts':ts,'event_ts':ts,'channel_type':'group'},**extra)
    if user is None:event.pop('user')
    return {'type':'event_callback','team_id':TEAM,'event_id':event_id or 'Ev'+ts.replace('.',''),'event':event}

class FakeSocket:
    """Stands in for slack_sdk's builtin SocketModeClient: the same listener lists, ack call and connection methods."""
    def __init__(self):
        self.message_listeners=[];self.socket_mode_request_listeners=[];self.on_close_listeners=[];self.on_error_listeners=[]
        self.connected=False;self.acks=[];self.on_ack=None;self.fail_connect=0;self.connects=0;self.closed=False
    def is_connected(self):return self.connected
    def connect_to_new_endpoint(self,force=False):
        self.connects+=1
        if self.fail_connect:self.fail_connect-=1;raise RuntimeError('Slack API returned invalid_auth')
        self.connected=True
    def send_socket_mode_response(self,response):
        if self.on_ack:self.on_ack(response)
        self.acks.append(response)
    def close(self):self.closed=True;self.connected=False
    def deliver(self,envelope_id,body,type='events_api'):
        for listener in self.socket_mode_request_listeners:listener(self,SimpleNamespace(type=type,envelope_id=envelope_id,payload=body))
    def hello(self):
        for listener in self.message_listeners:listener(self,{'type':'hello'},'{"type":"hello"}')

class Seats:
    """Per-seat bot clients for reactions; records who reacted to what."""
    def __init__(self,error=None):self.calls=[];self.made=[];self.error=error
    def __call__(self,cfg,seat):
        self.made.append(seat);outer=self
        class Client:
            def call(self,method,data):
                outer.calls.append((seat,method,data['timestamp'],data['name'],data['channel']))
                if outer.error:raise RuntimeError('Slack API returned '+outer.error)
                return {'ok':True}
        return Client()
    def reacted(self):return sorted((seat,ts) for seat,_,ts,_,_ in self.calls)

class History:
    """conversations.history over a fixed message list; oldest is exclusive, like Slack's default."""
    def __init__(self,cfg,messages):self.cfg=cfg;self.messages=messages;self.oldest=[]
    def call(self,method,data):
        self.oldest.append(data['oldest'])
        return {'ok':True,'messages':[dict(m) for m in self.messages if float(m['ts'])>float(data['oldest'])]}

def inbox(store,ts):
    with store.db() as db:return {r[0]:(r[1],r[2]) for r in db.execute('SELECT name,status,can_reply FROM notification_inbox WHERE ts=?',(ts,))}
def event_row(store,ts):
    with store.db() as db:return db.execute('SELECT event FROM notification_events WHERE ts=?',(ts,)).fetchone()[0]

def stored(store):
    with store.db() as db:return [r[0] for r in db.execute('SELECT ts FROM notification_events ORDER BY CAST(ts AS REAL)')]

class SocketCase(LabCase):
    def setUp(self):
        super().setUp()
        self.cfg.credentials_dir=self.dir
        self.token_file=self.dir/'slack-claude-app.env';self.token_file.write_text('SLACK_APP_TOKEN=xapp-1-test-only\n');self.token_file.chmod(0o600)
        self.s=self.store();self.fake=FakeSocket();self.seats=Seats();self.tokens=[]
        self.heard=Heard(self.cfg,self.s,self.seats)
        self.intake=self.make()
    def make(self,**kw):
        intake=Intake(self.cfg,self.s,kw.pop('heard',self.heard),factory=lambda t:self.tokens.append(t) or self.fake,**kw)
        self.assertTrue(intake.start());return intake

class SocketIngestTests(SocketCase):
    def test_message_event_is_ingested_before_it_is_acked(self):
        at_ack=[]
        self.fake.on_ack=lambda r:at_ack.append(stored(self.s))
        self.fake.deliver('E1',payload('10.000100','Codex, what changed?'))
        self.assertEqual(self.fake.acks,[{'envelope_id':'E1'}]);self.assertEqual(at_ack,[['10.000100']])
        self.assertEqual([r['status'] for r in self.s.rows('codex')],['queued'])
        self.assertEqual(self.s.cursor('0'),'0','socket intake must not move the poll cursor')
        self.assertTrue(self.tokens[0].startswith('xapp-'));self.assertNotIn('xapp-',json.dumps(self.intake.health()))
        self.assertIsNotNone(self.intake.health()['lastEventAt'])
    def test_failed_ingest_is_not_acked_and_succeeds_on_redelivery(self):
        with mock.patch.object(self.s,'ingest',side_effect=RuntimeError('database is locked')):self.fake.deliver('E1',payload('10.000100'))
        self.assertEqual(self.fake.acks,[]);self.assertIn('locked',self.intake.health()['lastError'])
        self.fake.deliver('E2',payload('10.000100'))
        self.assertEqual(self.fake.acks,[{'envelope_id':'E2'}]);self.assertEqual(stored(self.s),['10.000100'])
    def test_duplicate_envelope_or_event_id_is_not_ingested_twice(self):
        calls=[];real=self.s.ingest
        self.s.ingest=lambda events,**kw:calls.append([e['ts'] for e in events]) or real(events,**kw)
        self.fake.deliver('E1',payload('11.000100',event_id='Ev1'))
        self.fake.deliver('E1',payload('11.000100',event_id='Ev1'))      # same envelope again
        self.fake.deliver('E2',payload('11.000100',event_id='Ev1'))      # Slack retry: new envelope, same event_id
        self.make().receive(SimpleNamespace(type='events_api',envelope_id='E3',payload=payload('11.000100',event_id='Ev1')))  # after a restart
        self.assertEqual(calls,[['11.000100']]);self.assertEqual([a['envelope_id'] for a in self.fake.acks],['E1','E1','E2'])
        self.assertEqual(stored(self.s),['11.000100'])
    def test_out_of_scope_events_are_acked_but_never_ingested(self):
        ignored={'other-channel':payload('12.000100',channel=OTHER_CHANNEL),
            'thread-reply':payload('12.000200',thread_ts='12.000100'),
            'edit':payload('12.000300',user=None,subtype='message_changed',message={'user':HUMAN,'text':'edited','ts':'12.000100'}),
            'delete':payload('12.000400',user=None,subtype='message_deleted',deleted_ts='12.000100'),
            'slackbot':payload('12.000500',user='USLACKBOT',text='Reminder: Codex, review?'),
            'stranger':payload('12.000600',user='U0STRANGER1'),
            'reaction':dict(payload('12.000700'),event={'type':'reaction_added','user':HUMAN,'reaction':'eyes'}),
            'other-team':dict(payload('12.000800'),team_id='T0OTHER'),
            'broadcast':payload('12.000900',subtype='thread_broadcast',thread_ts='12.000100')}
        for i,(name,body) in enumerate(ignored.items()):self.fake.deliver(f'E{i}',body)
        self.fake.deliver('S1',{'command':'/x'},type='slash_commands')
        self.assertEqual(len(self.fake.acks),len(ignored)+1);self.assertEqual(stored(self.s),[])
        self.assertEqual(self.seats.calls,[])
    def test_own_posts_are_context_for_others_and_never_delivered_back(self):
        self.fake.deliver('E1',payload('13.000100','Codex here: tests pass.',user=BOT['codex']))
        self.assertEqual(stored(self.s),['13.000100']);self.assertEqual(self.s.rows('codex'),[])
        self.assertEqual(len(self.s.rows('claude')),1)
    def test_socket_ingest_waits_for_the_ingest_lock(self):
        # A relay pause notice is posted and recorded under ingest_lock; a socket event arriving in between waits for it.
        done=threading.Event()
        with ingest_lock(self.cfg):
            t=threading.Thread(target=lambda:(self.fake.deliver('E1',payload('14.000100','Grok in Cursor, review the diff?',user=BOT['claude'])),done.set()))
            t.start();time.sleep(0.3)
            self.assertEqual(self.fake.acks,[])
        t.join(5);self.assertTrue(done.is_set());self.assertEqual(self.fake.acks,[{'envelope_id':'E1'}])
        with self.s.db() as db:self.assertEqual(json.loads(db.execute('SELECT event FROM notification_events').fetchone()[0])['lead_origin'],'lead')
        self.assertTrue(self.s.rows('grok')[0]['can_reply'])

class IntervalAndFallbackTests(SocketCase):
    def test_connected_uses_reconcile_seconds_disconnected_uses_poll_seconds(self):
        self.assertEqual(self.intake.health()['mode'],'socket')
        self.fake.connected=True;self.assertEqual(self.intake.interval(),120);self.assertTrue(self.intake.health()['connected'])
        self.fake.connected=False;self.assertEqual(self.intake.interval(),20)
        self.cfg.data['slack']['reconcile_seconds']=300;self.fake.connected=True;self.assertEqual(self.intake.interval(),300)
    def test_missing_token_falls_back_to_polling_and_says_so(self):
        self.token_file.unlink();intake=Intake(self.cfg,self.s,factory=lambda t:self.fake)
        self.assertFalse(intake.start());h=intake.health()
        self.assertEqual((h['mode'],h['connected'],h['intervalSeconds']),('polling',False,20));self.assertIn('no app-level token',h['lastError'])
        self.assertEqual(health(self.cfg,self.s,[],None,None,intake)['intake']['mode'],'polling')
    def test_missing_slack_sdk_falls_back_to_polling_and_says_so(self):
        with mock.patch.object(socket_intake,'SocketModeClient',None):
            intake=Intake(self.cfg,self.s);self.assertFalse(intake.start())
        self.assertEqual(intake.health()['mode'],'polling');self.assertIn('slack_sdk is not installed',intake.health()['lastError'])
    def test_unsafe_or_wrong_token_file_falls_back_without_leaking(self):
        self.token_file.chmod(0o644);intake=Intake(self.cfg,self.s,factory=lambda t:self.fake)
        self.assertFalse(intake.start());self.assertIn('private',intake.health()['lastError'])
        self.token_file.chmod(0o600);self.token_file.write_text('SLACK_APP_TOKEN='+'xoxb-'+'bot-token-not-app\n')
        intake=Intake(self.cfg,self.s,factory=lambda t:self.fake);self.assertFalse(intake.start())
        self.assertIn('not an app-level token',intake.health()['lastError']);self.assertNotIn('xoxb',json.dumps(intake.health()))
    def test_app_token_filename_is_configurable(self):
        self.cfg.data['slack']['app_token_file']='custom-app.env';intake=Intake(self.cfg,self.s,factory=lambda t:self.fake)
        self.assertFalse(intake.start());self.assertIn('custom-app.env',intake.health()['lastError'])
    def test_sdk_detection_matches_this_interpreter(self):
        self.assertEqual(socket_intake.SocketModeClient is not None,importlib.util.find_spec('slack_sdk') is not None)
    @unittest.skipUnless(importlib.util.find_spec('slack_sdk'),'slack_sdk is not installed; polling-only path covered above')
    def test_fake_socket_matches_the_real_builtin_client_surface(self):
        client=socket_intake.SocketModeClient(app_token='xapp-'+'1-test-only',auto_reconnect_enabled=True);self.addCleanup(client.close)
        for name in ('message_listeners','socket_mode_request_listeners','on_close_listeners','on_error_listeners'):self.assertIsInstance(getattr(client,name),list,name)
        for name in ('is_connected','connect_to_new_endpoint','send_socket_mode_response','close'):self.assertTrue(callable(getattr(client,name)),name)
        self.assertFalse(client.is_connected())
    def test_first_connect_failure_retries_with_backoff(self):
        fake=FakeSocket();fake.fail_connect=1;self.fake=fake
        intake=Intake(self.cfg,self.s,factory=lambda t:fake);self.assertTrue(intake.start())
        self.assertFalse(intake.connected);self.assertIn('invalid_auth',intake.health()['lastError'])
        intake.ensure(now=time.time());self.assertEqual(fake.connects,1,'retry waits for the backoff')
        intake.ensure(now=time.time()+6);self.assertTrue(intake.connected);self.assertEqual(intake.interval(),120)
        intake.stop();self.assertTrue(fake.closed)

class ReconnectTests(SocketCase):
    def test_reconnect_wakes_a_catch_up_that_recovers_missed_messages(self):
        history=History(self.cfg,[{'user':HUMAN,'text':'Old note.','ts':'19.000100'}])
        poll_once(self.cfg,self.s,history,'0');self.assertEqual(self.s.cursor('0'),'19.000100')
        self.fake.hello();self.assertTrue(self.intake.wake.is_set());self.assertEqual(self.intake.health()['reconnects'],0)
        self.intake.wake.clear()
        self.fake.deliver('E1',payload('20.000200','Second note.'))  # pushed; 20.000100 was missed while reconnecting
        history.messages+=[{'user':HUMAN,'text':'Missed note.','ts':'20.000100'},{'user':HUMAN,'text':'Second note.','ts':'20.000200'}]
        self.intake.error='RuntimeError: Slack API returned invalid_auth'
        self.fake.hello();self.assertTrue(self.intake.wake.is_set());self.assertEqual(self.intake.health()['reconnects'],1)
        self.assertIsNone(self.intake.health()['lastError'])
        fresh=poll_once(self.cfg,self.s,history,'0')
        self.assertEqual(history.oldest[-1],'19.000100');self.assertEqual([e['ts'] for e in fresh],['20.000100'])
        self.assertEqual(stored(self.s),['19.000100','20.000100','20.000200']);self.assertEqual(self.s.cursor('0'),'20.000200')
    def test_edit_that_adds_a_mention_wakes_that_seat(self):
        # Live miss: a post edited to add "@Claude Code" after intake stayed buffered context and nobody answered.
        s=self.s;s.preference('claude','mentions_only');s.preference('codex','mentions_only')
        ts=f'{time.time()-120:.6f}';later=f'{time.time()-60:.6f}'  # history reads reach back an hour for edits
        history=History(self.cfg,[{'user':HUMAN,'text':'Codex, what changed?','ts':ts}])
        poll_once(self.cfg,s,history,'0',self.heard)
        self.assertEqual(inbox(s,ts)['claude'],('buffered',0))
        history.messages=[{'user':HUMAN,'text':f'Codex, what changed? <@{BOT["claude"]}>','ts':ts,'edited':{'user':HUMAN,'ts':later}}]
        poll_once(self.cfg,s,history,'0',self.heard)
        self.assertEqual(inbox(s,ts)['claude'],('queued',1))
        self.assertEqual(inbox(s,ts)['codex'],('queued',1),'a seat that could already answer is left as it was')
        self.assertIn('<@'+BOT['claude']+'>',json.loads(event_row(s,ts))['text'])
        # The same edit seen again changes nothing, and a seat that already answered is never re-queued.
        with s.db() as db:db.execute("UPDATE notification_inbox SET status='replied' WHERE ts=?",(ts,))
        poll_once(self.cfg,s,history,'0',self.heard)
        self.assertEqual(inbox(s,ts)['claude'],('replied',1))
        self.assertIn(('claude',ts),self.seats.reacted())
    def test_peer_edits_are_not_replanned(self):
        s=self.s;ts=f'{time.time()-120:.6f}';history=History(self.cfg,[{'user':BOT['grok'],'text':'Notes.','ts':ts}])
        poll_once(self.cfg,s,history,'0')
        history.messages=[{'user':BOT['grok'],'text':f'Notes. <@{BOT["codex"]}> please redo it','ts':ts,'edited':{'user':BOT['grok'],'ts':f'{time.time()-60:.6f}'}}]
        poll_once(self.cfg,s,history,'0')
        self.assertEqual(inbox(s,ts)['codex'][1],0)
    def test_close_wakes_the_poller(self):
        self.fake.on_close_listeners[0](1006,'abnormal');self.assertTrue(self.intake.wake.is_set())

class HeardReactionTests(SocketCase):
    def ingest(self,*events):return self.s.ingest([dict(team=TEAM,channel=CHANNEL,**e) for e in events])
    def test_trusted_post_naming_or_mentioning_seats_reacts_from_each_seat(self):
        self.heard.process(self.ingest({'user':HUMAN,'ts':'30.000100','text':f'Muse Code: thanks, great review. <@{BOT["codex"]}> too.'},{'user':HUMAN,'ts':'30.000200','text':'FYI the build is green.'}))
        # The untagged post names no seat, so the lead's bot shows it was heard.
        self.assertEqual(self.seats.reacted(),[('claude','30.000200'),('codex','30.000100'),('muse','30.000100')])
        self.assertTrue(all(c[1]=='reactions.add' and c[3]=='eyes' and c[4]==CHANNEL for c in self.seats.calls))
    def test_lead_post_reacts_but_not_from_its_own_seat(self):
        self.heard.process(self.ingest({'user':BOT['claude'],'ts':'31.000100','text':'Grok in Cursor: thanks. Claude Code too.'}))
        self.assertEqual(self.seats.reacted(),[('grok','31.000100')])
    def test_peer_bot_posts_never_react(self):
        self.heard.process(self.ingest({'user':BOT['grok'],'ts':'32.000100','text':'Muse Code, thanks!'}))
        self.assertEqual(self.seats.calls,[])
    def test_muted_seats_are_skipped(self):
        self.s.preference('cursor','muted')
        self.heard.process(self.ingest({'user':HUMAN,'ts':'33.000100','text':'Cursor Composer and Codex: thanks.'}))
        self.assertEqual(self.seats.reacted(),[('codex','33.000100')])
    def test_once_per_seat_and_ts_across_restarts_and_both_intakes(self):
        events=self.ingest({'user':HUMAN,'ts':'34.000100','text':'Codex, thanks.'})
        self.heard.process(events);self.heard.process(events);Heard(self.cfg,self.s,self.seats).process(events)
        self.fake.deliver('E1',payload('34.000100','Codex, thanks.'))   # socket sees it after the poller did
        self.assertEqual(self.seats.reacted(),[('codex','34.000100')]);self.assertEqual(self.seats.made,['codex'])
    def test_socket_and_poll_intake_both_react_after_ingest(self):
        order=[];self.fake.on_ack=lambda r:order.append('ack')
        real=self.heard.react;self.heard.react=lambda n,ts:order.append('react') or real(n,ts)
        self.fake.deliver('E1',payload('35.000100','Muse Code: thanks.'))
        poll_once(self.cfg,self.s,History(self.cfg,[{'user':HUMAN,'text':'Codex: thanks.','ts':'35.000200'}]),'0',self.heard)
        self.assertEqual(order,['ack','react','react']);self.assertEqual(self.seats.reacted(),[('codex','35.000200'),('muse','35.000100')])
    def test_already_reacted_is_fine_and_other_failures_never_block_intake(self):
        self.seats.error='already_reacted';self.fake.deliver('E1',payload('36.000100','Codex: thanks.'))
        self.seats.error='missing_scope';self.fake.deliver('E2',payload('36.000200','Muse Code: thanks.'))
        self.assertEqual([a['envelope_id'] for a in self.fake.acks],['E1','E2']);self.assertEqual(stored(self.s),['36.000100','36.000200'])
        with self.s.db() as db:self.assertEqual(dict(db.execute('SELECT name,status FROM heard_reactions').fetchall()),{'codex':'reacted','muse':'failed: RuntimeError'})
    def test_background_worker_reacts_off_the_ack_path(self):
        self.heard.start();self.addCleanup(self.heard.stop)
        self.fake.deliver('E1',payload('37.000100','Codex: thanks.'))
        for _ in range(50):
            if self.seats.calls:break
            time.sleep(0.02)
        self.assertEqual(self.seats.reacted(),[('codex','37.000100')])

if __name__=='__main__':unittest.main()
