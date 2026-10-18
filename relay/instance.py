"""Per-channel relay instance. Every team/channel/seat/session/posture value comes from config.json."""
import json,subprocess
from pathlib import Path

RELAY_ROOT=Path(__file__).resolve().parent
PROVIDERS={'claude','cursor_agent','muse','acp','codex','none'}
PROTOCOLS={'json','frame'}
TOOLS={'harness-default','read-only','none'}          # harness-default keeps the harness's normal tools and MCP servers
ROLE_POLICIES={None,'review-only'}                    # optional; unset means no role restriction
CLAUDE_GATED={'manual','dontAsk','plan'}              # never bypassPermissions/auto/acceptEdits
CODEX_APPROVALS={'granular-reject-all','on-request','untrusted'}  # never 'never'
MUSE_APPROVALS={'on-request','untrusted'}
ACP_PERMISSIONS={'deny','allow_once'}                 # answer to ACP session/request_permission
# Slack-triggered shell: off or sandboxed by default; interactive allowlists never carry over. Only modes each CLI can enforce.
SHELL_SUPPORT={'claude':{'off','harness-default'},'cursor_agent':{'sandboxed','harness-default'},'codex':{'sandboxed'},
    'muse':{'off','sandboxed'},'acp':{'harness-default'},'none':{'off','sandboxed','harness-default'}}
SHELL_DEFAULT={'claude':'off','cursor_agent':'sandboxed','codex':'sandboxed','muse':'sandboxed','acp':'harness-default','none':'off'}
# inherit (default): run each harness exactly as the user runs it. locked (opt-in): the hardened flags below.
POSTURES={'inherit','locked'}
INHERIT_WARNING='inherit posture: anything an agent can do interactively it can do when triggered from Slack.'
def posture_of(seat_cfg):return seat_cfg.get('posture','inherit')
def shell_of(seat_cfg):return seat_cfg.get('shell',SHELL_DEFAULT[seat_cfg.get('provider','none')])
# Claude Read deny rules (deny beats the user's interactive Read(///**) allow): credentials and relay state, never the seat's own clone.
CLAUDE_DENY_READ=['{credentials_dir}/**','{instance}/deliveries.sqlite*','{instance}/sessions/**','{instance}/diagnostics/**','~/.ssh/**']

class Instance:
    def __init__(self,data,instance_dir):
        self.data=data;self.dir=Path(instance_dir).expanduser().resolve()
        s=data['slack']
        self.name=data['instance'];self.team=s['team'];self.channel=s['channel']
        self.poll_seat=s['poll_seat'];self.poll_seconds=int(s.get('poll_seconds',120))
        self.credentials_dir=Path(s['credentials_dir']).expanduser()
        self.credential_file=s.get('credential_file','slack-{seat}.env');self.credential_key=s.get('credential_key','SLACK_BOT_TOKEN')
        self.trusted=dict(data['trusted_humans'])
        self.seats={n:dict(v) for n,v in data['seats'].items()}
        self.bots={n:v['bot_user_id'] for n,v in self.seats.items()}
        self.lead=data['lead']['seat']
        self.source_repo=Path(data['source_repo']).expanduser() if data.get('source_repo') else None
        self.project=data['project']
        # Whose team this is, for prompts; defaults to the first trusted human's name.
        self.owner=data.get('owner') or next(iter(self.trusted.values()),'the owner')
        self.reply_words=int(data.get('reply_max_words',150))
        self.context_max_chars=int(data.get('context_max_chars',32000))
        self.validate()

    def validate(self):
        if not (self.team and self.channel and self.trusted and self.seats):raise ValueError('Instance needs team, channel, trusted humans and seats')
        if len(set(self.bots.values()))!=len(self.bots) or set(self.bots.values())&set(self.trusted):raise ValueError('Seat bot IDs must be unique and distinct from humans')
        if self.lead not in self.seats or self.poll_seat not in self.seats:raise ValueError('Lead and poll seat must be configured seats')
        for n,s in self.seats.items():
            if s.get('provider','none') not in PROVIDERS or s.get('protocol','json') not in PROTOCOLS:raise ValueError('Unknown provider/protocol for '+n)
            if not s.get('app_name'):raise ValueError('Seat needs its plain app name: '+n)
            if s.get('tools','harness-default') not in TOOLS or s.get('role_policy') not in ROLE_POLICIES:raise ValueError('Unknown tools posture or role policy for '+n)
            if s.get('permission_mode','manual') not in CLAUDE_GATED:raise ValueError('Ungated Claude permission mode for '+n)
            if posture_of(s) not in POSTURES:raise ValueError('Unknown posture for '+n)
            if shell_of(s) not in SHELL_SUPPORT[s.get('provider','none')]:raise ValueError(f'Shell mode {shell_of(s)} is not enforceable for {n}')
            if s.get('approval_policy','on-request') not in CODEX_APPROVALS or s.get('approval_mode','on-request') not in MUSE_APPROVALS:raise ValueError('Ungated approval setting for '+n)
            if s.get('acp_permission','deny') not in ACP_PERMISSIONS:raise ValueError('Unknown ACP permission answer for '+n)
            # yolo mirrors a user who runs this harness without approvals; a locked seat is the opposite choice.
            if s.get('yolo') and posture_of(s)=='locked':raise ValueError('A locked seat cannot also be yolo: '+n)

    def path(self,value):
        p=Path(value).expanduser()
        return p if p.is_absolute() else self.dir/p
    def provider(self,seat):return self.seats[seat].get('provider','none')
    def can_reply(self,seat):return self.provider(seat)!='none'
    def workers(self):return [n for n in self.seats if self.can_reply(n)]
    def seat_cwd(self,seat):return self.path(self.seats[seat].get('cwd',f'work/{seat}'))
    def tools(self,seat):return self.seats[seat].get('tools','harness-default')
    def shell(self,seat):return shell_of(self.seats[seat])
    def posture(self,seat):return posture_of(self.seats[seat])
    def read_denies(self,seat):
        s=self.seats[seat];out=[]
        for pat in s.get('deny_read',CLAUDE_DENY_READ if s.get('provider')=='claude' else []):
            pat=pat.format(credentials_dir=self.credentials_dir,instance=self.dir)
            out.append(f"Read({'/'+pat if pat.startswith('/') else pat})")  # //abs/path or ~/path, per the CLI's rule syntax
        return out
    def session_file(self,seat):return self.dir/'sessions'/f'{seat}.json'
    @property
    def context_path(self):return self.path(self.data.get('context_file','TEAM_CONTEXT.md'))
    @property
    def diagnostics(self):
        d=self.dir/'diagnostics';d.mkdir(mode=0o700,exist_ok=True);return d

def ensure_workdirs(cfg):
    """Give each worker seat its own scratch clone of source_repo; its origin is the source checkout, so pushed branches land there for the lead to integrate."""
    made=[]
    for seat in cfg.workers():
        d=cfg.seat_cwd(seat)
        if d.exists():continue
        d.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        if not cfg.source_repo:d.mkdir(mode=0o700);made.append(seat);continue
        subprocess.run(['git','clone','--local','--quiet',str(cfg.source_repo),str(d)],check=True,capture_output=True)
        made.append(seat)
    return made

def load(instance_dir):
    d=Path(instance_dir).expanduser().resolve()
    return Instance(json.loads((d/'config.json').read_text()),d)
