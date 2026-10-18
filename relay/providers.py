"""Provider sessions for one relay instance; session state lives under the instance dir.
Posture per seat ("tools"): harness-default keeps the harness's normal tools and MCP servers; read-only and none restrict them.
Every run is pinned to the harness's gated permission mode: anything that needs approval is denied, never auto-approved."""
import json,os,queue,re,subprocess,tempfile,threading,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from instance import CLAUDE_GATED,shell_of,posture_of
from routing import client_response

SECRET=re.compile(r'(?:sk-ant-|sk-|xox[baprs]-)[A-Za-z0-9_-]{8,}')
def clean(s):return SECRET.sub('[REDACTED]',s or '')
def now():return datetime.now(timezone.utc)

# Flags that bypass or auto-approve permissions. Refused even if a config adds them through extra_args.
FORBIDDEN={'--dangerously-skip-permissions','--allow-dangerously-skip-permissions','bypassPermissions','--force','-f','--yolo','--approve-mcps',
    '--dangerously-bypass-approvals-and-sandbox','--approve-for-me','--dangerously-bypass-hook-trust','--disable-approval','--disable-sandbox','--auto-review','--ignore-user-config'}
def assert_gated(args,prompt=None):
    body=[a for a in args if a is not prompt]
    bad=[a for a in body if a in FORBIDDEN or 'danger-full-access' in a or 'approval_policy="never"' in a or 'auto_review' in a]
    values=lambda flag:[body[i+1] if i+1<len(body) else '' for i,x in enumerate(body) if x==flag]  # every occurrence; a later one wins in the CLI
    if any(v not in CLAUDE_GATED for v in values('--permission-mode')):bad.append('--permission-mode')
    if any(v!='off' for v in values('--approval-judge')):bad.append('--approval-judge')
    if any(v!='enabled' for v in values('--sandbox')):bad.append('--sandbox')
    if bad:raise RuntimeError('Refusing ungated provider flags: '+', '.join(bad))
    return args

def waiting(cfg,seat,at=None):
    """Optional per-seat activation gate (for example, wait for a usage-credit reset); off unless activate_after is set."""
    after=cfg.seats[seat].get('activate_after')
    return bool(after) and (at or now())<datetime.fromisoformat(after)

def load_state(cfg,seat,fresh):
    p=cfg.session_file(seat)
    if p.exists():return json.loads(p.read_text())
    state=dict(fresh,instance=cfg.name,seat=seat,cwd=str(cfg.seat_cwd(seat)),tools=cfg.tools(seat),created_at=now().isoformat(),initialized=False)
    save_state(cfg,seat,state);return state
def save_state(cfg,seat,state):
    p=cfg.session_file(seat);p.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2));tmp.replace(p)

def env_for(seat_cfg):
    # Launchd PATH is minimal; node-based CLIs (codex) need their own bin dir. Never switch to API-key billing.
    env={k:v for k,v in os.environ.items() if not k.startswith(('ANTHROPIC_','CLAUDE_CODE_USE_'))}
    env['PATH']=str(Path(seat_cfg['executable']).parent)+':'+env.get('PATH','/usr/bin:/bin')
    return env
def extra(seat_cfg):return list(seat_cfg.get('extra_args',[]))
def locked(seat_cfg):return posture_of(seat_cfg)=='locked'

# ---- Claude Code: normal setting sources, tools and MCP servers; manual mode with nobody to answer prompts = denied
def claude_args(s,state,prompt,deny_reads=()):
    flag='--resume' if state['initialized'] else '--session-id'
    # --tools/--disallowedTools are variadic: they must be followed by another flag, never by the prompt.
    args=[s['executable'],'-p','--output-format','json','--model',s['model'],flag,state['session_id']]
    # inherit: the user's own settings, default mode, tools and MCP servers. `--permission-prompts none` only keeps a headless
    # run from waiting on a prompt nobody is there to answer; it changes no permission the user configured.
    if not locked(s):return args+extra(s)+['--permission-prompts','none',prompt]
    deny=(['Bash'] if shell_of(s)=='off' else [])+list(deny_reads)  # overrides interactive user allowlists (bare Bash, Read(///**))
    if deny:args+=['--disallowedTools',*deny]
    tools=s.get('tools','harness-default')
    if tools!='harness-default':args+=['--tools','Read,Glob,Grep' if tools=='read-only' else '','--strict-mcp-config','--mcp-config','{"mcpServers":{}}']
    return args+extra(s)+['--permission-mode',s.get('permission_mode','manual'),'--permission-prompts','none',prompt]
def parse_claude(stdout,model):
    result=json.loads(stdout)
    if result.get('is_error') or result.get('subtype')!='success' or not result.get('result','').strip():raise RuntimeError('Claude returned no successful response')
    if model not in result.get('modelUsage',{}):raise RuntimeError('Requested Claude model is not verified')
    return result['result']
def claude_usage(stdout):
    r=json.loads(stdout);return {k:r[k] for k in ('usage','modelUsage','total_cost_usd','num_turns') if k in r}

# ---- cursor-agent: normal mode and configured MCPs; no --force/--yolo/--approve-mcps, so unapproved actions are refused
def cursor_args(s,state,prompt):
    args=[s['executable'],'-p','--trust','--model',s['model'],'--resume',state['chat_id'],'--output-format','json']
    if not locked(s):return args+extra(s)+[prompt]  # inherit: the CLI's configured mode, sandbox, allowlist and MCPs
    if s.get('tools','harness-default')!='harness-default':args+=['--mode','ask']
    if shell_of(s)=='sandboxed':args+=['--sandbox','enabled']  # overrides the CLI config's disabled sandbox
    return args+extra(s)+[prompt]
def parse_cursor(stdout):
    result=json.loads(stdout)
    if result.get('is_error') or result.get('subtype')!='success' or not result.get('result'):raise RuntimeError('Provider returned no successful result')
    return result['result']
def cursor_usage(stdout):return {'usage':json.loads(stdout).get('usage')}

# ---- Muse Code: normal preset and tools; approval on, LLM approval judge off (it would auto-approve)
def muse_args(s,state,cwd,prompt):
    if not locked(s):return [s['executable'],'exec','--json','--session-id',state['session_id'],'--workspace',str(cwd)]+(['--model',s['model']] if s.get('model') else [])+extra(s)+[prompt]
    args=[s['executable'],'exec','--json','--session-id',state['session_id'],'--workspace',str(cwd),'--approval-mode',s.get('approval_mode','on-request'),'--approval-judge','off']
    tools=s.get('tools','harness-default')
    if shell_of(s)=='off' and tools=='harness-default':args+=['--disable-shell']
    if tools=='read-only':args+=['--disable-write','--disable-shell']
    elif tools=='none':args+=['--preset','empty','--disable-write','--disable-shell','--disable-web-tools']
    if s.get('model'):args+=['--model',s['model']]
    return args+extra(s)+[prompt]
def parse_muse(stdout):
    events=[json.loads(line) for line in stdout.splitlines() if line.strip()]
    completed=[x['payload'] for x in events if x.get('payload_type')=='run.terminal.completed']
    if not completed or completed[-1].get('terminal')!='completed' or not completed[-1].get('text','').strip():raise RuntimeError('Muse returned no complete response')
    if any(x.get('payload_type')=='run.terminal.failed' for x in events):raise RuntimeError('Muse failed')
    return completed[-1]['text']
def muse_model(stdout):
    found=[json.loads(l).get('payload',{}).get('model_id') for l in stdout.splitlines() if '"run.model.configured"' in l]
    return found[-1] if found else None
def muse_usage(stdout):
    events=[json.loads(l) for l in stdout.splitlines() if l.strip()]
    keep=[dict({k:v for k,v in e.get('payload',{}).items() if k not in ('text','prompt')},type=e.get('payload_type')) for e in events if any(w in str(e.get('payload_type','')) for w in ('usage','token','context'))]
    return {'model':muse_model(stdout),'events':keep[-3:]}
def run_muse(cmd,cwd,timeout=180):
    """Returns the raw JSONL up to the terminal event. Terminal completion is authoritative; some CLI builds hang during shutdown."""
    with tempfile.TemporaryFile() as err:
        p=subprocess.Popen(cmd,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
        events=queue.Queue();lines=[];deadline=time.monotonic()+timeout
        def read():
            try:
                for line in p.stdout:events.put(line)
            finally:events.put(None)
        reader=threading.Thread(target=read,daemon=True);reader.start()
        try:
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:raise TimeoutError('Muse returned no terminal completion before timeout')
                try:line=events.get(timeout=remaining)
                except queue.Empty:raise TimeoutError('Muse returned no terminal completion before timeout')
                if line is None:
                    if p.wait(timeout=5):raise RuntimeError('Muse process failed')
                    parse_muse(''.join(lines));return ''.join(lines)
                if not line.strip():continue
                lines.append(line);event=json.loads(line)
                if event.get('payload_type') in ('run.terminal.completed','run.terminal.failed'):
                    parse_muse(''.join(lines));return ''.join(lines)
        finally:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait()
            reader.join(timeout=5);p.stdout.close()

# ---- Codex: user config (MCP servers, hooks) kept; only the dangerous parts are overridden with -c, which takes precedence.
# granular-reject-all: every approval category (sandbox escalation, rules, permission requests, MCP elicitations) is
# automatically rejected instead of prompting; exec mode also refuses command/patch/permission approvals outright.
CODEX_APPROVAL={'granular-reject-all':'approval_policy={granular={sandbox_approval=false,rules=false,request_permissions=false,mcp_elicitations=false}}',
    'on-request':'approval_policy="on-request"','untrusted':'approval_policy="untrusted"'}
# codex exec records approval_policy=never whatever is passed, so MCP calls cannot be approval-gated headless. Servers and
# plugins that act outside the machine or drive the desktop are disabled for Slack-triggered runs instead.
def codex_user_config(home=None):
    try:import tomllib
    except ImportError:raise RuntimeError('A locked Codex seat needs Python 3.11+ (tomllib) to read the Codex config; refusing to run it ungated') from None
    try:return tomllib.loads((Path(home or os.environ.get('CODEX_HOME',Path.home()/'.codex'))/'config.toml').read_text())
    except (OSError,ValueError):return {}
def codex_disables(s):
    """Locked: every MCP server in the user config is off unless in codex_mcp_allow (new servers default to off), and every enabled
    plugin is off unless in codex_plugin_allow (plugins supply servers such as messages and cua_repl; a server-name override for
    a plugin server breaks config loading). Plugin keys are unquoted."""
    user=codex_user_config();allow=set(s.get('codex_mcp_allow',['openaiDeveloperDocs']));plugin_allow=set(s.get('codex_plugin_allow',[]))
    out=[x for n in user.get('mcp_servers',{}) if n not in allow for x in ('-c',f'mcp_servers.{n}.enabled=false')]
    return out+[x for p,v in user.get('plugins',{}).items() if p not in plugin_allow and (v or {}).get('enabled',True) for x in ('-c',f'plugins.{p}.enabled=false')]
def codex_args(s,state,cwd,prompt):
    model=['-m',s['model'],'-c',f'model_reasoning_effort="{s.get("reasoning_effort","high")}"']
    if not locked(s):  # inherit: the user's codex config as-is (its sandbox, approval policy, MCP servers, hooks)
        if state.get('thread_id'):return [s['executable'],'exec','resume','--json',*model,*extra(s),state['thread_id'],prompt]
        return [s['executable'],'exec','-C',str(cwd),'--json',*model,*extra(s),prompt]
    tools=s.get('tools','harness-default');sandbox='workspace-write' if tools=='harness-default' else 'read-only'
    # workspace-write confined to the seat's scratch clone: no extra roots, no /tmp or $TMPDIR, no network.
    confine=['-c','sandbox_workspace_write.writable_roots=[]','-c','sandbox_workspace_write.network_access=false',
        '-c','sandbox_workspace_write.exclude_slash_tmp=true','-c','sandbox_workspace_write.exclude_tmpdir_env_var=true']
    common=['--json','-c',f'sandbox_mode="{sandbox}"',*confine,'-c',CODEX_APPROVAL[s.get('approval_policy','on-request')],'-c','approvals_reviewer="user"',
        *codex_disables(s),
        '-m',s['model'],'-c',f'model_reasoning_effort="{s.get("reasoning_effort","high")}"',*extra(s)]
    if state.get('thread_id'):return [s['executable'],'exec','resume',*common,state['thread_id'],prompt]
    return [s['executable'],'exec','-s',sandbox,'-C',str(cwd),*common,prompt]
def codex_events(stdout):return [json.loads(l) for l in stdout.splitlines() if l.strip().startswith('{')]
def parse_codex(stdout):
    events=codex_events(stdout)
    if any(e.get('type') in ('error','turn.failed') for e in events):raise RuntimeError('Codex turn failed')
    if not any(e.get('type')=='turn.completed' for e in events):raise RuntimeError('Codex returned no completed turn')
    thread=next((e['thread_id'] for e in events if e.get('type')=='thread.started'),None)
    texts=[e['item'].get('text','') for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
    if not texts or not texts[-1].strip():raise RuntimeError('Codex returned no final message')
    return thread,texts[-1]
def codex_usage(stdout):
    turns=[e.get('usage') for e in codex_events(stdout) if e.get('type')=='turn.completed']
    return {'usage':turns[-1] if turns else None}

# ---- ACP (Antigravity): mode pinned to "default"; permission requests answered per acp_permission (deny unless configured)
def select_review_model(acp,config,model):
    options={x['id']:x for x in config.get('configOptions',[])}
    values={x['value'] for x in options.get('model',{}).get('options',[])}
    base,_,level=model.rpartition('-')
    if model in values:
        config,_=acp.call('session/set_config_option',{'sessionId':acp.session,'configId':'model','value':model})
        expected={'model':model}
    elif base in values and any(x['value']==level for x in options.get('thinking_level',{}).get('options',[])):
        for key,value in [('model',base),('thinking_level',level)]:
            config,_=acp.call('session/set_config_option',{'sessionId':acp.session,'configId':key,'value':value})
        expected={'model':base,'thinking_level':level}
    else:raise RuntimeError('Required model unavailable; no substitution')
    actual={x['id']:x.get('currentValue') for x in config.get('configOptions',[])}
    if any(actual.get(k)!=v for k,v in expected.items()):raise RuntimeError('Model/thinking selection failed')
    return config

class ACP:
    def __init__(self,cfg,seat):
        s=cfg.seats[seat];self.events=queue.Queue();self.seq=0;self.session=None;self.policy=s.get('acp_permission','deny')
        cwd=cfg.seat_cwd(seat);mcp=list(s.get('mcp_servers',[]))
        home=cfg.path(s.get('home',f'{seat}-home'));(home/'antigravity-acp').mkdir(mode=0o700,parents=True,exist_ok=True)
        settings=home/'antigravity-acp'/'settings.json'
        if not settings.exists():settings.write_text(json.dumps({'auth':{'type':'oauth-personal'}},indent=2))
        self.err=open(cfg.diagnostics/f'{seat}-stderr.log','a')
        self.p=subprocess.Popen([s['executable']],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1,cwd=cwd,env=dict(os.environ,GEMINI_HOME=str(home)))
        threading.Thread(target=self.read,daemon=True).start()
        self.call('initialize',{'protocolVersion':1,'clientCapabilities':{},'clientInfo':{'name':f'{cfg.name}-relay','version':'1.0'}})
        self.call('authenticate',{'methodId':'oauth-personal'})
        state=load_state(cfg,seat,{'session_id':None})
        if state.get('session_id'):
            self.session=state['session_id'];self.call('session/load',{'sessionId':self.session,'cwd':str(cwd),'mcpServers':mcp})
        else:
            result,_=self.call('session/new',{'cwd':str(cwd),'mcpServers':mcp})
            self.session=result['sessionId'];state['session_id']=self.session;save_state(cfg,seat,state)
        # locked pins the gated "default" mode; inherit uses the configured acp_mode (the runtime's default is "default").
        want='default' if locked(s) else s.get('acp_mode','default')
        mode,_=self.call('session/set_config_option',{'sessionId':self.session,'configId':'mode','value':want})
        if not any(x.get('id')=='mode' and x.get('currentValue')==want for x in mode['configOptions']):raise RuntimeError('Requested ACP mode not active')
        self.config=select_review_model(self,mode,s['model'])
        (cfg.diagnostics/f'{seat}-config.json').write_text(json.dumps(self.config,indent=2))
    def read(self):
        for line in self.p.stdout:
            try:self.events.put(json.loads(line))
            except ValueError:pass
        self.events.put({'closed':True})
    def send(self,x):self.p.stdin.write(json.dumps(x)+'\n');self.p.stdin.flush()
    def call(self,method,params,timeout=180):
        self.seq+=1;rid=self.seq;chunks=[];deadline=time.monotonic()+timeout
        self.send({'jsonrpc':'2.0','id':rid,'method':method,'params':params})
        while time.monotonic()<deadline:
            try:m=self.events.get(timeout=max(0.01,min(1,deadline-time.monotonic())))
            except queue.Empty:continue
            if m.get('closed'):raise RuntimeError('ACP closed')
            if 'method' in m and 'id' in m:
                self.send(client_response(m,self.policy));continue
            if m.get('method')=='session/update':
                u=m.get('params',{}).get('update',{})
                if u.get('sessionUpdate')=='agent_message_chunk':chunks.append(u.get('content',{}).get('text',''))
            if m.get('id')==rid:
                if 'error' in m:raise RuntimeError('ACP error '+str(m['error'].get('code')))
                return m.get('result',{}),''.join(chunks)
        raise TimeoutError('ACP timed out; transport must close')
    def close(self):
        self.p.terminate()
        try:self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:self.p.kill();self.p.wait()
        self.err.close()

class Providers:
    """respond() returns {'text': reply, 'usage': token/context usage as reported by the CLI} for the batch record."""
    def __init__(self,cfg):self.cfg=cfg
    def timeout(self,seat):return int(self.cfg.seats[seat].get('timeout_seconds',180))

    def run(self,seat,args,prompt=None):
        if locked(self.cfg.seats[seat]):assert_gated(args,prompt)
        # stdin closed: codex appends piped stdin to the prompt and claude waits for it.
        p=subprocess.run(args,cwd=self.cfg.seat_cwd(seat),env=env_for(self.cfg.seats[seat]),stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=self.timeout(seat))
        # Keep diagnostic output private, redacting likely credentials before persistence.
        (self.cfg.diagnostics/f'{seat}-last-output.txt').write_text(clean(p.stdout))
        (self.cfg.diagnostics/f'{seat}-last-error.log').write_text(clean(p.stderr))
        if p.returncode:raise RuntimeError(f'{seat} process failed; inspect private diagnostics')
        return p.stdout

    def respond(self,seat,prompt):
        s=self.cfg.seats[seat];kind=s.get('provider','none')
        if kind=='claude':
            if waiting(self.cfg,seat):raise RuntimeError('Seat activation gate is closed')
            state=load_state(self.cfg,seat,{'session_id':str(uuid.uuid4()),'requested_model':s['model']})
            state['last_attempt_at']=now().isoformat();save_state(self.cfg,seat,state)
            out=self.run(seat,claude_args(s,state,prompt,self.cfg.read_denies(seat)),prompt);reply=parse_claude(out,s['model'])
            state.update(initialized=True,verified_model=s['model']);save_state(self.cfg,seat,state)
            return {'text':reply,'usage':claude_usage(out)}
        if kind=='cursor_agent':
            state=load_state(self.cfg,seat,{'chat_id':None,'requested_model':s['model']})
            if not state.get('chat_id'):
                chat=self.run(seat,[s['executable'],'create-chat']).strip().splitlines()[-1].strip()
                if not re.fullmatch(r'[0-9a-f-]{36}',chat):raise RuntimeError('cursor-agent create-chat returned no chat id')
                state['chat_id']=chat;save_state(self.cfg,seat,state)
            out=self.run(seat,cursor_args(s,state,prompt),prompt);reply=parse_cursor(out)
            state['initialized']=True;save_state(self.cfg,seat,state)
            return {'text':reply,'usage':cursor_usage(out)}
        if kind=='muse':
            state=load_state(self.cfg,seat,{'session_id':str(uuid.uuid4())})
            args=muse_args(s,state,self.cfg.seat_cwd(seat),prompt)
            if locked(s):assert_gated(args,prompt)
            raw=run_muse(args,self.cfg.seat_cwd(seat),self.timeout(seat))
            state.update(initialized=True,observed_model=muse_model(raw));save_state(self.cfg,seat,state)
            return {'text':parse_muse(raw),'usage':muse_usage(raw)}
        if kind=='codex':
            state=load_state(self.cfg,seat,{'thread_id':None,'requested_model':s['model']})
            out=self.run(seat,codex_args(s,state,self.cfg.seat_cwd(seat),prompt),prompt);thread,reply=parse_codex(out)
            if not state.get('thread_id'):
                if not thread:raise RuntimeError('Codex did not report a thread id')
                state['thread_id']=thread
            state['initialized']=True;save_state(self.cfg,seat,state)
            return {'text':reply,'usage':codex_usage(out)}
        if kind=='acp':
            acp=ACP(self.cfg,seat)
            try:
                result,reply=acp.call('session/prompt',{'sessionId':acp.session,'prompt':[{'type':'text','text':prompt}]},timeout=self.timeout(seat))
                if result.get('stopReason')!='end_turn' or not reply.strip():raise RuntimeError('No complete response')
                state=load_state(self.cfg,seat,{});state['initialized']=True;save_state(self.cfg,seat,state)
                return {'text':reply,'usage':{k:result[k] for k in ('usage','_meta') if k in result}}
            finally:acp.close()
        raise RuntimeError(f'Seat {seat} is context-only; no provider worker')
