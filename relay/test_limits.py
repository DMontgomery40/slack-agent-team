"""Owner decisions: addressed-only wakes with buffered context; 150 turns/day; pause after 4 idle hours."""
import json,time,unittest
from service import process_one,announce_pause
from relay_testlib import LabCase,event,bid_of,rev_of,BOT

def answer(name,p):
    if name=='antigravity':return f'BKRV1 {bid_of(p)}\nMEMORY\nok\nREPLY NONE\nEND {bid_of(p)}'
    return json.dumps({'receipt':bid_of(p),'reply':f'{name} reply','context_revision':rev_of(p)})

class BufferedContextTests(LabCase):
    def test_unaddressed_messages_ride_along_with_next_addressed_turn(self):
        s=self.store();s.preference('codex','mentions_only')
        s.ingest([event(ts='5.001',text='The deploy window is Friday.'),event(ts='5.002',text='FYI the schema changed.')])
        self.assertIsNone(s.claim('codex'),'buffered context alone must never wake a seat')
        s.ingest([event(ts='5.003',text='Codex, what does the schema change break?')])
        b=s.claim('codex')
        self.assertEqual([e['ts'] for e in b['events']],['5.001','5.002','5.003'])
        self.assertEqual([e['reply'] for e in b['events']],[False,False,True])
    def test_buffer_is_capped_and_older_context_is_dropped(self):
        s=self.store();s.preference('codex','mentions_only')
        s.ingest([event(ts=f'6.{i:03d}',text=f'note {i}') for i in range(1,31)]+[event(ts='6.100',text='Codex, summarize?')])
        b=s.claim('codex');cap=s.limits()['buffer_context_max']
        self.assertEqual(len(b['events']),cap+1);self.assertEqual(b['events'][-1]['ts'],'6.100')
        with s.db() as db:self.assertEqual(db.execute("SELECT count(*) FROM notification_inbox WHERE name='codex' AND status='buffered'").fetchone()[0],0)
    def test_follow_conversation_seat_is_unchanged(self):
        s=self.store();s.ingest([event(ts='7.001',text='What is next?')])
        self.assertEqual([e['ts'] for e in s.claim('claude')['events']],['7.001'])

class LimitTests(LabCase):
    def test_daily_budget_stops_new_turns(self):
        s=self.store();now=time.time()
        with s.db() as db:
            for i in range(int(s.limits()['daily_turns'])):db.execute("INSERT INTO notification_batches(id,name,status,created,response,public_reply,slack_ts,error) VALUES(?,?,'processed',?,'','','','')",(f'b{i}','codex',now-60))
        s.ingest([event(ts=f'{now:.6f}',text='Codex, still there?')])
        self.assertEqual(s.paused(),'budget');self.assertIsNone(s.claim('codex'))
    def test_relay_notices_do_not_count_against_the_budget(self):
        s=self.store()
        for i in range(5):s.record_notice('paused',f'8.00{i}')
        self.assertEqual(s.limit_status()['turns_last_24h'],0)
    def test_idle_pause_and_resume_on_next_human_post(self):
        s=self.store();old=time.time()-5*3600;s.mark_started(old)
        s.ingest([event(ts=f'{old:.6f}',text='Codex, check this?')])
        self.assertEqual(s.paused(),'idle');self.assertIsNone(s.claim('codex'))
        s.ingest([event(ts=f'{time.time():.6f}',text='Codex, are you there?')])
        self.assertIsNone(s.paused());self.assertIsNotNone(s.claim('codex'))
    def test_peer_bot_posts_do_not_reset_the_idle_clock(self):
        s=self.store();old=time.time()-5*3600;s.mark_started(old)
        s.ingest([event(ts=f'{time.time():.6f}',text='Status update from a bot.',user=BOT['codex'])])
        self.assertEqual(s.paused(),'idle')
    def test_pause_notice_posts_once_per_episode_and_is_recorded_as_relay(self):
        s=self.store();old=time.time()-5*3600;s.mark_started(old);posts=[]
        post=lambda text:posts.append(text) or '9.500'
        self.assertEqual(announce_pause(self.cfg,s,post),'idle');self.assertIsNone(announce_pause(self.cfg,s,post))
        self.assertEqual(len(posts),1);self.assertIn('No ACK needed',posts[0])
        s.ingest([event(ts='9.500',text=posts[0],user=BOT[self.cfg.lead])])
        with s.db() as db:ev=json.loads(db.execute("SELECT event FROM notification_events WHERE ts='9.500'").fetchone()[0])
        self.assertEqual(ev.get('lead_origin'),'relay')

class LeadSeatAndParserTests(LabCase):
    def test_addressed_only_lead_seat_still_answers_untagged_human_requests(self):
        s=self.store();s.preference('claude','mentions_only')
        s.ingest([event(ts='11.001',text='What is the relay status?')])
        b=s.claim('claude');self.assertTrue(b and b['events'][-1]['reply'])
    def test_addressed_only_lead_seat_does_not_wake_on_peer_replies(self):
        s=self.store();s.preference('claude','mentions_only')
        s.ingest([event(ts='12.001',text='ACK: research done, sources below.',user=BOT['codex'])])
        self.assertIsNone(s.claim('claude'))
    def test_parser_accepts_prose_before_a_fenced_json_reply(self):
        from notifications import parse_result
        raw='Researching first.\n```json\n{"receipt": "b1", "reply": "ACK: done"}\n```'
        self.assertEqual(parse_result(raw,'b1')['reply'],'ACK: done')
        self.assertEqual(parse_result('Note: {"receipt": "b2", "reply": null}','b2')['reply'],None)
        with self.assertRaises(ValueError):parse_result('Prose only, no JSON.','b3')

class DefaultModeTests(unittest.TestCase):
    def test_shipped_example_starts_every_seat_addressed_only(self):
        import tempfile,json
        from pathlib import Path
        from instance import Instance
        from notifications import Store
        from relay_testlib import EXAMPLE
        with tempfile.TemporaryDirectory() as d:
            cfg=Instance(json.loads(EXAMPLE.read_text()),Path(d))
            s=Store(Path(d)/'deliveries.sqlite',cfg)
            self.assertEqual({n:p['mode'] for n,p in s.preferences().items()},{n:'mentions_only' for n in cfg.bots})

if __name__=='__main__':unittest.main()
