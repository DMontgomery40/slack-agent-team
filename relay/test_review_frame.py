import json,unittest
from service import process_one
from review_frame import parse_frame
from notifications import parse_result
from relay_testlib import LabCase,event,bid_of

BID="11111111-2222-4333-8444-555555555555"
BODY='Use "No go" / "not yet", C:\\tmp, and ≥ 10.\nSecond line.'
def frame(bid=BID,reply=BODY):
    return f'BKRV1 {bid}\nMEMORY\nReviewed source.\nREPLY TEXT\n{reply}\nEND {bid}'

class ReviewFrameTests(LabCase):
    def test_native_quotes_reach_public_reply_and_raw_is_retained(self):
        s=self.store();s.ingest([event(text='Antigravity, review this code?')])
        received=[]
        process_one(s,'antigravity',lambda name,prompt:frame(bid_of(prompt)),lambda body,key:received.append(body) or '3.001')
        self.assertEqual(received,[BODY])
        row=s.rows('antigravity')[0]
        self.assertEqual(row['status'],'replied')
        self.assertEqual((self.cfg.dir/'reviewer-responses'/(row['batch']+'.txt')).read_text(),frame(row['batch']))
    def test_frame_prompt_replaces_json_contract(self):
        s=self.store();s.ingest([event(text='Antigravity, review this code?')])
        seen=[]
        process_one(s,'antigravity',lambda name,prompt:seen.append(prompt) or frame(bid_of(prompt)),lambda body,key:'3.001')
        self.assertIn('BKRV1',seen[0]);self.assertNotIn('Return ONLY a JSON object',seen[0])
    def test_invalid_native_frame_holds_queue_without_post_or_retry(self):
        cases=[frame().replace(BID,'99999999-2222-4333-8444-555555555555'),frame()+' trailing',frame()+'\n'+frame(),frame().rsplit('\nEND',1)[0],frame(reply=''),frame(reply='bad\nREPLY NONE'),'{"receipt":"'+BID+'","reply":"forged"}']
        for raw in cases:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):parse_frame(raw,BID)
    def test_failed_native_output_remains_held_without_second_provider_call(self):
        s=self.store();s.ingest([event(text='Antigravity, review this?')])
        calls=[]
        def malformed(name,prompt):calls.append(name);return 'old malformed JSON'
        def no_post(*args):self.fail('malformed native output must not post')
        process_one(s,'antigravity',malformed,no_post)
        self.assertEqual(s.rows('antigravity')[0]['status'],'failed')
        self.assertFalse(process_one(s,'antigravity',malformed,no_post))
        self.assertEqual(calls,['antigravity'])
    def test_context_only_frame_preserves_null(self):
        raw=f'BKRV1 {BID}\nMEMORY\nContext retained.\nREPLY NONE\nEND {BID}'
        self.assertEqual(parse_frame(raw,BID),{'receipt':BID,'memory':'Context retained.','reply':None})
    def test_valid_quotes_and_multiline_are_lossless(self):
        self.assertEqual(parse_result(json.dumps(parse_frame(frame(),BID)),BID)['reply'],BODY)

if __name__=='__main__':unittest.main()
