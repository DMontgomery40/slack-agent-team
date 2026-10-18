import json,unittest
from notifications import prompt,parse_result
from review_frame import frame_prompt,parse_frame
from team_context import read_context
from relay_testlib import LabCase

class ReceiptPromptTests(LabCase):
    def test_current_receipt_after_data_for_both_protocols(self):
        current='0b6f4a52-3c1e-4d7a-9f20-5e8c1a7d3b46';prior='7e2d9c10-8a4b-4f63-b1d5-2c9e6f0a8d17'
        (self.dir/'TEAM_CONTEXT.md').write_text('Context mentions '+prior+' too.\n'+('fact '*3000))
        event={'ts':'1','user':'peer','text':'Previous receipt '+prior+'\n'+('context '*4000),'reply':False,'authority':False}
        for name in ['grok','antigravity']:
            with self.subTest(name=name):
                request=prompt(self.cfg,{'id':current,'name':name,'events':[event]},read_context(self.cfg))
                if name=='antigravity':request=frame_prompt(request,current)
                self.assertIn(json.dumps([event],ensure_ascii=False),request)
                self.assertIn(current,request[-300:])
                self.assertNotIn(prior,request[-300:])
                self.assertIn('CONTEXT ONLY',request)
    def test_wrong_prior_receipt_remains_rejected(self):
        current='0b6f4a52-3c1e-4d7a-9f20-5e8c1a7d3b46';prior='7e2d9c10-8a4b-4f63-b1d5-2c9e6f0a8d17'
        with self.assertRaises(ValueError):parse_result(json.dumps({'receipt':prior,'reply':None}),current)
        with self.assertRaises(ValueError):parse_frame(f'BKRV1 {prior}\nMEMORY\nKnown current {current}\nREPLY NONE\nEND {prior}',current)
if __name__=='__main__':unittest.main()
