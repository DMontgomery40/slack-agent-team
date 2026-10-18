"""Push intake: the lead seat's app holds one Socket Mode connection that feeds the durable store; polling becomes reconciliation.
Without an app-level token or slack_sdk the relay polls exactly as before. Also the ingest-time "heard" reaction for both intakes."""
import json,os,queue,sys,threading,time
import routing
from lead_ledger import ingest_lock
from providers import clean
try:
    from slack_sdk.socket_mode.builtin import SocketModeClient
except ImportError:
    SocketModeClient=None

def app_token_path(cfg):return cfg.credentials_dir/cfg.data['slack'].get('app_token_file','slack-claude-app.env')

def app_token(cfg):
    """SLACK_APP_TOKEN from the private app token file, or None when the file does not exist yet. Never printed."""
    p=app_token_path(cfg)
    if not p.exists():return None
    if p.stat().st_mode & 0o077 or p.stat().st_uid!=os.getuid():raise RuntimeError('Credential file must be private and owned by current user')
    values=dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x)
    token=values.get('SLACK_APP_TOKEN','').strip()
    if not token.startswith('xapp-'):raise RuntimeError('SLACK_APP_TOKEN is missing or is not an app-level token')
    return token

def socket_message(cfg,payload):
    """An events_api payload as a history-shaped message, or None when intake would reject it. Same accepted() rule as polling:
    other channels, thread replies, edits, deletes and Slackbot are dropped; own posts go on to ingest, which skips the sender's seat."""
    e=payload.get('event') or {}
    if payload.get('type')!='event_callback' or e.get('type')!='message':return None
    msg={k:v for k,v in e.items() if k not in ('channel_type','event_ts')}
    if 'team' not in msg and payload.get('team_id'):msg['team']=payload['team_id']
    return dict(msg,team=cfg.team) if routing.accepted(cfg,msg) else None

class Intake:
    """Socket Mode receiver: ingest under ingest_lock, then ack, then react. Every hello wakes the poller for a catch-up."""
    def __init__(self,cfg,store,heard=None,factory=None,wake=None):
        self.cfg=cfg;self.store=store;self.heard=heard;self.factory=factory;self.wake=wake or threading.Event()
        self.client=None;self.mode='polling';self.last_event=None;self.hellos=0;self.error=None
        self.next_try=0;self.backoff=5
        with store.db() as db:db.execute('CREATE TABLE IF NOT EXISTS socket_deliveries(event_id TEXT PRIMARY KEY,envelope_id TEXT,ts TEXT,received REAL)')

    def start(self):
        try:token=app_token(self.cfg)
        except Exception as exc:self.error='polling only: '+type(exc).__name__+': '+clean(str(exc))[:200];return False
        if not token:self.error=f'polling only: no app-level token at {app_token_path(self.cfg)}';return False
        factory=self.factory or (SocketModeClient and (lambda t:SocketModeClient(app_token=t,auto_reconnect_enabled=True)))
        if not factory:self.error='polling only: slack_sdk is not installed for '+sys.executable;return False
        self.client=factory(token);self.mode='socket';self.error=None
        self.client.message_listeners.append(self.on_message)
        self.client.socket_mode_request_listeners.append(self.on_request)
        self.client.on_close_listeners.append(self.on_close)
        self.client.on_error_listeners.append(self.on_error)
        self.ensure()
        return True

    def ensure(self,now=None):
        """The SDK reconnects on its own only after a first successful connect, so retry here with backoff until it does."""
        now=now or time.time()
        if not self.client or self.client.is_connected() or now<self.next_try:return
        try:self.client.connect_to_new_endpoint();self.backoff=5
        except Exception as exc:
            self.error=type(exc).__name__+': '+clean(str(exc))[:200];self.next_try=now+self.backoff;self.backoff=min(self.backoff*2,300)
            print(json.dumps({'socketConnectFailure':self.error}),flush=True)

    @property
    def connected(self):return bool(self.client and self.client.is_connected())
    def interval(self):return int(self.cfg.data['slack'].get('reconcile_seconds',120)) if self.connected else self.cfg.poll_seconds
    def health(self):
        return {'mode':self.mode,'connected':self.connected,'lastEventAt':self.last_event,'reconnects':max(0,self.hellos-1),'lastError':self.error,'intervalSeconds':self.interval()}

    def on_message(self,client,message,raw=None):
        if message.get('type')!='hello':return
        self.hellos+=1;self.error=None  # lastError covers the current connection
        print(json.dumps({'socketConnected':True,'reconnects':max(0,self.hellos-1)}),flush=True)
        self.wake.set()  # catch-up runs on the main loop through fetch(client,store.cursor(old)) under ingest_lock

    def on_close(self,code=None,reason=None):
        print(json.dumps({'socketClosed':code}),flush=True)
        self.wake.set()  # reconcile now; the next wait uses poll_seconds while disconnected

    def on_error(self,exc):self.error=type(exc).__name__+': '+clean(str(exc))[:200]

    def on_request(self,client,req):
        try:fresh=self.receive(req)
        except Exception as exc:
            # No ack: Slack redelivers, and reconciliation polling covers it if it never succeeds.
            self.error=type(exc).__name__+': '+clean(str(exc))[:200]
            print(json.dumps({'socketIngestFailure':self.error}),flush=True);return
        client.send_socket_mode_response({'envelope_id':req.envelope_id})
        if fresh and self.heard:self.heard.submit(fresh)

    def receive(self,req):
        """Durable ingest before the ack. Socket ingest never moves the poll cursor, so reconciliation still sees anything missed."""
        if req.type!='events_api':return []
        payload=req.payload or {};key=payload.get('event_id') or 'envelope:'+req.envelope_id
        self.last_event=time.time()
        with self.store.db() as db:
            if db.execute('SELECT 1 FROM socket_deliveries WHERE event_id=? OR envelope_id=?',(key,req.envelope_id)).fetchone():return []
        msg=socket_message(self.cfg,payload);fresh=[]
        if msg:
            with ingest_lock(self.cfg):fresh=self.store.ingest([msg],advance_cursor=False)
        with self.store.db() as db:
            # Recorded only after a successful ingest, so a failed ingest is retried on redelivery.
            db.execute('INSERT OR IGNORE INTO socket_deliveries VALUES(?,?,?,?)',(key,req.envelope_id,msg['ts'] if msg else '',time.time()))
            db.execute('DELETE FROM socket_deliveries WHERE received<?',(time.time()-7*86400,))
        return fresh

    def stop(self):
        if self.client:
            try:self.client.close()
            except Exception:pass

class Heard:
    """Ingest-time "heard" reaction, no model turn: a new trusted-human or lead post that mentions or names a seat gets
    that seat's reaction from its own bot. Once per (seat, ts), claimed before the call; a failure is logged and never blocks intake."""
    def __init__(self,cfg,store,slack=None):
        self.cfg=cfg;self.store=store;self.slack=slack;self.clients={};self.pending=queue.Queue();self.thread=None
        with store.db() as db:db.execute('CREATE TABLE IF NOT EXISTS heard_reactions(name TEXT,ts TEXT,status TEXT,at REAL,PRIMARY KEY(name,ts))')

    def seats(self,event,prefs):
        sender=event.get('user')
        if not (sender in self.cfg.trusted or event.get('lead_origin')=='lead'):return []
        text=event.get('text','') or '';names=routing.named(self.cfg,text)
        return [n for n,u in self.cfg.bots.items() if (f'<@{u}>' in text or n in names) and sender!=u and prefs.get(n,{}).get('mode')!='muted']

    def react(self,name,ts):
        if name not in self.clients:self.clients[name]=self.slack(self.cfg,name)
        try:self.clients[name].call('reactions.add',{'channel':self.cfg.channel,'timestamp':ts,'name':self.cfg.data.get('heard_reaction','eyes')})
        except RuntimeError as exc:
            if 'already_reacted' not in str(exc):raise

    def process(self,events):
        if not events:return
        prefs=self.store.preferences()
        for e in events:
            for name in self.seats(e,prefs):
                with self.store.db() as db:
                    if not db.execute("INSERT OR IGNORE INTO heard_reactions VALUES(?,?,'claimed',?)",(name,e['ts'],time.time())).rowcount:continue
                status='reacted'
                try:self.react(name,e['ts'])
                except Exception as exc:
                    status='failed: '+type(exc).__name__
                    print(json.dumps({'heardReactionError':name,'ts':e['ts'],'errorType':type(exc).__name__}),flush=True)
                with self.store.db() as db:db.execute('UPDATE heard_reactions SET status=? WHERE name=? AND ts=?',(status,name,e['ts']))

    def submit(self,events):
        """Off the ack and ingest_lock path once started; synchronous before start() (tests)."""
        if not events:return
        if self.thread:self.pending.put(list(events))
        else:self.process(events)

    def start(self):
        def run():
            while True:
                events=self.pending.get()
                if events is None:return
                try:self.process(events)
                except Exception as exc:print(json.dumps({'heardWorkerError':type(exc).__name__}),flush=True)
        self.thread=threading.Thread(target=run,name='heard',daemon=True);self.thread.start()

    def stop(self):
        if self.thread:self.pending.put(None)
