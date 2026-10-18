import unittest,tempfile
from pathlib import Path
import routing
class RoutingTests(unittest.TestCase):
    def test_claim_is_durable_and_not_replayed_after_ambiguous_delivery(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.sqlite';q=routing.Ledger(p)
            self.assertTrue(q.claim('grok:1'));self.assertFalse(q.claim('grok:1'))
            q.close();q=routing.Ledger(p);self.assertFalse(q.claim('grok:1'));q.close()
    def test_reviewer_never_approves_tool_permissions(self):
        request={'id':19,'method':'session/request_permission','params':{'options':[{'optionId':'yes','kind':'allow_always'}]}}
        self.assertEqual(routing.client_response(request),{'jsonrpc':'2.0','id':19,'result':{'outcome':{'outcome':'cancelled'}}})
        self.assertEqual(routing.client_response({'id':20,'method':'fs/write_text_file'})['error']['code'],-32601)
    def test_acp_permission_denies_by_rejecting_unless_configured(self):
        opts={'id':3,'method':'session/request_permission','params':{'options':[{'optionId':'a1','kind':'allow_once'},{'optionId':'r1','kind':'reject_once'}]}}
        self.assertEqual(routing.client_response(opts)['result'],{'outcome':{'outcome':'selected','optionId':'r1'}})
        self.assertEqual(routing.client_response(opts,'allow_once')['result'],{'outcome':{'outcome':'selected','optionId':'a1'}})
if __name__=='__main__':unittest.main()
