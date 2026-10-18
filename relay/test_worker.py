import json,unittest
from service import process_one
from relay_testlib import LabCase,event,bid_of,BOT

class WorkerTests(LabCase):
    def setUp(self):super().setUp();self.s=self.store()

    def test_silent_context_then_question_and_duplicate_no_second_turn(self):
        self.s.ingest([event()])
        def provider(name,prompt):return json.dumps({'receipt':bid_of(prompt),'reply':'noted','memory':'blue'})
        def no_post(*args):self.fail('routine context must not post')
        self.assertTrue(process_one(self.s,'muse',provider,no_post))
        self.assertFalse(process_one(self.s,'muse',provider,no_post))
        self.s.ingest([event('2.001',text='Muse, what color?')])
        def answer(name,prompt):return json.dumps({'receipt':bid_of(prompt),'reply':'Blue.'})
        self.assertTrue(process_one(self.s,'muse',answer,lambda text,key:'3.001'))
        self.assertEqual(self.s.rows('muse')[-1]['status'],'replied')
        self.s.ingest([event('2.001',text='Muse, what color?')])
        self.assertFalse(process_one(self.s,'muse',answer,no_post))

    def test_gate_never_invokes_provider_and_mute_during_call_suppresses_post(self):
        self.s.ingest([event(text=f'<@{BOT["grok"]}> answer?')])
        def never(*a):self.fail('gate must prevent invocation')
        self.assertFalse(process_one(self.s,'claude',never,never,True))
        def provider(name,prompt):
            self.s.preference('grok','muted')
            return json.dumps({'receipt':bid_of(prompt),'reply':'Hello'})
        process_one(self.s,'grok',provider,never)
        self.assertEqual(self.s.rows('grok')[0]['status'],'processed')

    def test_ambiguous_post_is_held_not_replayed(self):
        self.s.ingest([event(text='Grok, explain the status?')])
        def provider(name,prompt):return json.dumps({'receipt':bid_of(prompt),'reply':'Pending.'})
        def failed_post(*a):raise TimeoutError('uncertain Slack post')
        process_one(self.s,'grok',provider,failed_post)
        self.assertEqual(self.s.rows('grok')[0]['status'],'failed')
        self.assertFalse(process_one(self.s,'grok',provider,failed_post))

if __name__=='__main__':unittest.main()
