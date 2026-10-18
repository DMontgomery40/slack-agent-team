import copy,json,os,pathlib,subprocess,sys,tempfile,unittest
from datetime import datetime,timezone
from unittest.mock import patch
import providers
from relay_testlib import LabCase,lab

class ArgvTests(LabCase):
    """Default posture: harness-normal tools and MCP servers, permission mode pinned to gated (deny, never auto-approve)."""
    def setUp(self):
        super().setUp()
        # Hermetic: never read the developer's real ~/.codex/config.toml. Tests that need a user config patch their own.
        p=patch('providers.codex_user_config',return_value={});p.start();self.addCleanup(p.stop)
    def argv(self,seat,state,patch=None):
        s=dict(self.cfg.seats[seat],**dict({'posture':'locked'},**(patch or {})));cwd=self.cfg.seat_cwd(seat)  # hardened flags are the locked posture
        build={'claude':lambda:providers.claude_args(s,dict({'session_id':'S','initialized':False},**state),'P',self.cfg.read_denies('claude')),'grok':lambda:providers.cursor_args(s,dict({'chat_id':'C'},**state),'P'),
            'cursor':lambda:providers.cursor_args(s,dict({'chat_id':'C'},**state),'P'),'muse':lambda:providers.muse_args(s,dict({'session_id':'M'},**state),cwd,'P'),
            'codex':lambda:providers.codex_args(s,dict({'thread_id':None},**state),cwd,'P')}[seat]
        return providers.assert_gated(build(),'P')
    def test_default_claude_keeps_mcp_and_tools_and_is_gated(self):
        args=self.argv('claude',{})
        self.assertNotIn('--strict-mcp-config',args);self.assertNotIn('--mcp-config',args);self.assertNotIn('--tools',args)
        self.assertNotIn('--setting-sources',args);self.assertNotIn('--safe-mode',args);self.assertNotIn('{"mcpServers":{}}',args)
        self.assertEqual(args[args.index('--permission-mode')+1],'manual');self.assertEqual(args[args.index('--permission-prompts')+1],'none')
        self.assertEqual(args[args.index('--model')+1],self.cfg.seats['claude']['model']);self.assertIn('--session-id',args)
        self.assertIn('--resume',self.argv('claude',{'initialized':True}))
        self.assertIn('--strict-mcp-config',self.argv('claude',{},{'tools':'none'}))
    def test_default_shell_is_off_or_sandboxed(self):
        c=self.argv('claude',{});self.assertEqual(c[c.index('--disallowedTools')+1],'Bash')
        rules=c[c.index('--disallowedTools')+1:c.index('--permission-mode')];self.assertEqual(c[-2:],['none','P'])  # variadic flag never swallows the prompt
        self.assertIn('Read(/'+str(self.cfg.credentials_dir)+'/**)',rules)
        self.assertFalse(any(str(self.cfg.seat_cwd('claude')) in r for r in rules))
        for t in ('read-only','none'):
            r=self.argv('claude',{},{'tools':t});self.assertTrue(r[r.index('--tools')+2].startswith('--'))
        self.assertNotIn('Bash',self.argv('claude',{},{'shell':'harness-default'}))
        for seat in ('grok','cursor'):
            a=self.argv(seat,{});self.assertEqual(a[a.index('--sandbox')+1],'enabled')
        self.assertIn('--disable-shell',self.argv('muse',{},{'shell':'off'}));self.assertNotIn('--disable-shell',self.argv('muse',{}))
        user={'mcp_servers':{'computer-use':{},'node_repl':{},'openaiDeveloperDocs':{},'brand-new-server':{}},'plugins':{'messages@openai-bundled':{'enabled':True},'google-calendar@openai-curated':{'enabled':False}}}
        with patch('providers.codex_user_config',return_value=user):a=self.argv('codex',{})
        for x in ['mcp_servers.computer-use.enabled=false','mcp_servers.node_repl.enabled=false','mcp_servers.brand-new-server.enabled=false','plugins.messages@openai-bundled.enabled=false']:self.assertIn(x,a)
        self.assertFalse(any('openaiDeveloperDocs' in x or 'google-calendar' in x for x in a));self.assertNotIn('--ignore-user-config',a)
        for seat,mode in [('claude','sandboxed'),('cursor','off'),('codex','harness-default'),('antigravity','off')]:
            with self.assertRaises(ValueError):lab(self.dir,**{seat:{'shell':mode}})
        with self.assertRaises(RuntimeError):self.argv('grok',{},{'extra_args':['--sandbox','disabled']})
    def test_default_cursor_agent_runs_normal_mode_without_force(self):
        for seat,model in [(n,self.cfg.seats[n]['model']) for n in ('grok','cursor')]:
            args=self.argv(seat,{})
            self.assertNotIn('--mode',args);self.assertEqual(args[args.index('--model')+1],model)
            for flag in ['--force','-f','--yolo','--approve-mcps']:self.assertNotIn(flag,args)
        self.assertIn('ask',self.argv('grok',{},{'tools':'read-only'}))
    def test_default_muse_runs_normal_preset_with_approval_and_no_judge(self):
        args=self.argv('muse',{})
        for flag in ['--preset','--disable-write','--disable-shell','--disable-web-tools','--user-input-auto-resolve','--yolo','--disable-approval','--disable-sandbox']:self.assertNotIn(flag,args)
        self.assertEqual(args[args.index('--approval-mode')+1],'on-request');self.assertEqual(args[args.index('--approval-judge')+1],'off')
        self.assertEqual(args[args.index('--workspace')+1],str(self.cfg.seat_cwd('muse')))
    def test_default_codex_keeps_user_config_but_pins_sandbox_and_approval(self):
        first=self.argv('codex',{});again=self.argv('codex',{'thread_id':'T'})
        self.assertEqual(first[1:4],['exec','-s','workspace-write']);self.assertEqual(first[first.index('-C')+1],str(self.cfg.seat_cwd('codex')))
        self.assertEqual(again[1:3],['exec','resume']);self.assertEqual(again[-2:],['T','P'])
        for args in (first,again):
            self.assertIn('sandbox_mode="workspace-write"',args);self.assertNotIn('--ignore-user-config',args)
            self.assertIn('approval_policy="on-request"',args)
            for c in ['sandbox_workspace_write.writable_roots=[]','sandbox_workspace_write.network_access=false','sandbox_workspace_write.exclude_slash_tmp=true','approvals_reviewer="user"']:self.assertIn(c,args)
            self.assertEqual(args[args.index('-m')+1],self.cfg.seats['codex']['model'])
        ro=self.argv('codex',{},{'tools':'read-only'})
        self.assertIn('sandbox_mode="read-only"',ro);self.assertNotIn('--ignore-user-config',ro)
    def test_gate_refuses_bypass_flags_even_from_config(self):
        for seat,bad in [('claude',['--dangerously-skip-permissions']),('claude',['--permission-mode','bypassPermissions']),('grok',['--force']),('cursor',['--yolo']),
                ('grok',['--approve-mcps']),('codex',['--dangerously-bypass-approvals-and-sandbox']),('codex',['-c','sandbox_mode="danger-full-access"']),('codex',['--ignore-user-config']),('codex',['-c','approvals_reviewer="auto_review"']),('grok',['--auto-review']),('muse',['--yolo']),('muse',['--approval-judge','on'])]:
            with self.subTest(seat=seat,bad=bad):
                with self.assertRaises(RuntimeError):self.argv(seat,{},{'extra_args':bad})
    def test_config_refuses_ungated_modes(self):
        for seat,patch in [('claude',{'permission_mode':'bypassPermissions'}),('claude',{'permission_mode':'auto'}),('codex',{'approval_policy':'never'}),('muse',{'approval_mode':'never'}),('antigravity',{'acp_permission':'allow_always'})]:
            with self.assertRaises(ValueError):lab(self.dir,**{seat:patch})
    def test_env_finds_node_cli_and_never_uses_api_key_billing(self):
        with patch.dict(os.environ,{'ANTHROPIC_API_KEY':'x','PATH':'/usr/bin'}):
            env=providers.env_for(self.cfg.seats['codex'])
        self.assertNotIn('ANTHROPIC_API_KEY',env);self.assertTrue(env['PATH'].startswith(str(pathlib.Path(self.cfg.seats['codex']['executable']).parent)+':'))

class CodexConfigTests(LabCase):
    def test_locked_codex_without_tomllib_fails_closed(self):
        s=dict(self.cfg.seats['codex'],posture='locked')
        with patch.dict(sys.modules,{'tomllib':None}):
            with self.assertRaisesRegex(RuntimeError,'3.11'):providers.codex_args(s,{'thread_id':None},self.cfg.seat_cwd('codex'),'P')

class StdinTests(LabCase):
    def test_provider_processes_get_closed_stdin(self):
        with patch('providers.subprocess.run') as run:
            run.return_value=subprocess.CompletedProcess([],0,'out','')
            providers.Providers(self.cfg).run('codex',['codex','exec','P'],'P')
        self.assertIs(run.call_args.kwargs['stdin'],subprocess.DEVNULL)

class InheritTests(LabCase):
    """Default posture: each harness runs exactly as the user runs it; the relay adds no restriction or approval override."""
    def test_lab_seats_inherit_and_add_no_restrictions(self):
        self.assertTrue(all(self.cfg.posture(n)=='inherit' for n in self.cfg.workers()))
        s=self.cfg.seats;cwd=self.cfg.seat_cwd
        c=providers.claude_args(s['claude'],{'session_id':'S','initialized':True},'P',self.cfg.read_denies('claude'))
        self.assertEqual(c[-3:],['--permission-prompts','none','P'])
        for flag in ['--disallowedTools','--permission-mode','--tools','--strict-mcp-config','--mcp-config','--setting-sources']:self.assertNotIn(flag,c)
        for seat in ('grok','cursor'):
            a=providers.cursor_args(s[seat],{'chat_id':'C'},'P')
            for flag in ['--sandbox','--mode','--force','--yolo']:self.assertNotIn(flag,a)
        m=providers.muse_args(s['muse'],{'session_id':'M'},cwd('muse'),'P')
        self.assertFalse(any(x.startswith(('--approval','--disable','--preset','--user-input')) for x in m))
        for state in ({'thread_id':None},{'thread_id':'T'}):
            x=providers.codex_args(s['codex'],state,cwd('codex'),'P')
            self.assertFalse(any(('sandbox' in a or 'approval' in a or 'mcp_servers' in a or 'plugins.' in a or a in ('-s','--ignore-user-config')) for a in x))
            self.assertEqual(x[x.index('-m')+1],self.cfg.seats['codex']['model'])
    def test_inherit_skips_the_locked_flag_gate(self):
        with patch('providers.subprocess.run') as run:
            run.return_value=subprocess.CompletedProcess([],0,'out','')
            providers.Providers(self.cfg).run('cursor',['cursor-agent','--force','P'],'P')
        cfg=lab(self.dir,cursor={'posture':'locked'})
        with self.assertRaises(RuntimeError):providers.Providers(cfg).run('cursor',['cursor-agent','--force','P'],'P')

class UsageTests(unittest.TestCase):
    def test_usage_is_extracted_for_rollover(self):
        c=json.dumps({'subtype':'success','result':'r','usage':{'input_tokens':5},'modelUsage':{'claude-model-id':{'contextWindow':200000}}})
        self.assertEqual(providers.claude_usage(c)['modelUsage']['claude-model-id']['contextWindow'],200000)
        self.assertEqual(providers.cursor_usage(json.dumps({'usage':{'inputTokens':9}})),{'usage':{'inputTokens':9}})
        x='\n'.join(json.dumps(e) for e in [{'type':'thread.started','thread_id':'T'},{'type':'turn.completed','usage':{'input_tokens':7}}])
        self.assertEqual(providers.codex_usage(x),{'usage':{'input_tokens':7}})
        m=json.dumps({'payload_type':'run.usage.updated','payload':{'input_tokens':3,'text':'hidden'}})
        self.assertEqual(providers.muse_usage(m)['events'],[{'input_tokens':3,'type':'run.usage.updated'}])

class TimeoutTests(LabCase):
    def test_per_seat_timeouts(self):
        p=providers.Providers(self.cfg)
        self.assertEqual((p.timeout('muse'),p.timeout('claude')),(300,180))

class ParseTests(unittest.TestCase):
    def test_claude_error_and_wrong_model_not_success(self):
        for result in [{'subtype':'success','is_error':True,'result':'bad'},{'subtype':'success','result':'ok','modelUsage':{'other-model':{}}}]:
            with self.assertRaises(RuntimeError):providers.parse_claude(json.dumps(result),'claude-model-id')
        self.assertEqual(providers.parse_claude(json.dumps({'subtype':'success','result':'ready','modelUsage':{'claude-model-id':{}}}),'claude-model-id'),'ready')
    def test_codex_jsonl(self):
        ok='\n'.join(json.dumps(e) for e in [{'type':'thread.started','thread_id':'T1'},{'type':'item.completed','item':{'type':'agent_message','text':'done'}},{'type':'turn.completed','usage':{}}])
        self.assertEqual(providers.parse_codex(ok),('T1','done'))
        with self.assertRaises(RuntimeError):providers.parse_codex(ok.replace('turn.completed','turn.failed'))
        with self.assertRaises(RuntimeError):providers.parse_codex(ok.rsplit('\n',1)[0])
    def test_muse_failed_terminal_is_not_success(self):
        with self.assertRaises(RuntimeError):providers.parse_muse(json.dumps({'payload_type':'run.terminal.failed','payload':{'terminal':'failed','text':'partial'}}))
        raw='\n'.join(json.dumps(e) for e in [{'payload_type':'run.model.configured','payload':{'model_id':'m-1'}},{'payload_type':'run.terminal.completed','payload':{'terminal':'completed','text':'R'}}])
        self.assertEqual((providers.parse_muse(raw),providers.muse_model(raw)),('R','m-1'))
    def test_cursor_requires_success(self):
        with self.assertRaises(RuntimeError):providers.parse_cursor(json.dumps({'subtype':'error','result':'x'}))

class GateTests(LabCase):
    patches={'claude':{'activate_after':'2999-01-01T00:00:00+00:00'}}
    def test_activation_gate_never_runs_model(self):
        self.assertTrue(providers.waiting(self.cfg,'claude'))
        with patch('providers.subprocess.run') as run:
            with self.assertRaisesRegex(RuntimeError,'gate'):providers.Providers(self.cfg).respond('claude','test')
            run.assert_not_called()
    def test_gate_defaults_off(self):
        self.assertFalse(any(providers.waiting(self.cfg,n) for n in self.cfg.seats if n!='claude'))

class MuseCompletionTests(unittest.TestCase):
    """Regression: accepting a native terminal result must not await CLI shutdown."""
    def invoke(self,events,linger=False):
        with tempfile.TemporaryDirectory() as tmp:
            home=pathlib.Path(tmp);exe=home/'muse';pidfile=home/'child.pid'
            script='#!'+sys.executable+'\nimport os,time\nfrom pathlib import Path\nPath('+repr(str(pidfile))+').write_text(str(os.getpid()))\n'
            for e in events:script+='print('+repr(json.dumps(e))+',flush=True)\n'
            if linger:script+='time.sleep(60)\n'
            exe.write_text(script);exe.chmod(0o700)
            value=providers.parse_muse(providers.run_muse([str(exe)],home,timeout=5))
            with self.assertRaises(ProcessLookupError):os.kill(int(pidfile.read_text()),0)
            return value
    def test_completed_receipt_returns_without_waiting_for_process_exit(self):
        e={'payload_type':'run.terminal.completed','payload':{'terminal':'completed','text':'{"receipt":"fixture","reply":null}'}}
        self.assertEqual(json.loads(self.invoke([e],linger=True)),{'receipt':'fixture','reply':None})
    def test_process_exit_without_terminal_completion_is_rejected(self):
        with self.assertRaises(RuntimeError):self.invoke([{'payload_type':'run.output.delta','payload':{'text':'partial'}}])
    def test_failed_terminal_is_rejected(self):
        with self.assertRaises(RuntimeError):self.invoke([{'payload_type':'run.terminal.failed','payload':{'terminal':'failed','text':'partial'}}])

def options(split=True):
    return {'configOptions':[{'id':'mode','currentValue':'default','options':[{'value':'default'}]},
        {'id':'model','currentValue':'fast-model' if split else 'review-model-medium','options':[{'value':'review-model' if split else 'review-model-high'}]},
        *([{'id':'thinking_level','currentValue':'medium','options':[{'value':'high'},{'value':'medium'}]}] if split else [])]}
class Wire:
    def __init__(self,config,ignore_thinking=False):self.config=copy.deepcopy(config);self.session='fixture';self.ignore_thinking=ignore_thinking
    def call(self,method,params):
        if method!='session/set_config_option':raise AssertionError('Unexpected RPC')
        for option in self.config['configOptions']:
            if option['id']==params['configId']:
                if params['value'] not in [o['value'] for o in option['options']]:raise RuntimeError('Unsupported option value')
                if not(self.ignore_thinking and option['id']=='thinking_level'):option['currentValue']=params['value']
        return copy.deepcopy(self.config),''
class ModelSelectionTests(unittest.TestCase):
    def select(self,wire):return providers.select_review_model(wire,wire.config,'review-model-high')
    def test_split_catalog_selects_argon_high_without_default_flash(self):
        state={o['id']:o['currentValue'] for o in self.select(Wire(options()))['configOptions']}
        self.assertEqual((state['model'],state['thinking_level'],state['mode']),('review-model','high','default'))
    def test_legacy_catalog_keeps_exact_combined_model(self):
        self.assertEqual(next(o['currentValue'] for o in self.select(Wire(options(False)))['configOptions'] if o['id']=='model'),'review-model-high')
    def test_rejects_runtime_that_ignores_high_thinking(self):
        with self.assertRaises(RuntimeError):self.select(Wire(options(),True))
    def test_rejects_catalog_without_required_model(self):
        config=options();config['configOptions'][1]['options']=[{'value':'fast-model'}]
        with self.assertRaises(RuntimeError):self.select(Wire(config))

if __name__=='__main__':unittest.main()
