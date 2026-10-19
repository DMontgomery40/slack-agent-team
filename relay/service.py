"""One relay instance = one channel: a poller plus one serial worker per seat over independent durable queues."""
import argparse,fcntl,json,os,re,signal,sys,threading,time,urllib.request,uuid
from datetime import datetime,timezone
import routing
from instance import load,ensure_workdirs,INHERIT_WARNING
from notifications import Store,prompt,parse_result
from providers import Providers,waiting,clean
from review_frame import frame_prompt,parse_frame
from team_context import read_context
from lead_ledger import ingest_lock
from socket_intake import Intake,Heard

def urllib_transport(method,data,token):
    r=urllib.request.Request('https://slack.com/api/'+method,data=json.dumps(data).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json; charset=utf-8'})
    with urllib.request.urlopen(r,timeout=20) as response:return json.load(response)

class Slack:
    def __init__(self,cfg,seat,transport=urllib_transport):
        self.cfg=cfg;self.seat=seat;self.transport=transport
        p=cfg.credentials_dir/cfg.credential_file.format(seat=seat)
        if p.stat().st_mode & 0o077 or p.stat().st_uid!=os.getuid():raise RuntimeError('Credential file must be private and owned by current user')
        values=dict(x.split('=',1) for x in p.read_text().splitlines() if '=' in x)
        self.token=values[cfg.credential_key].strip()
        a=self.call('auth.test',{})
        if a.get('team_id')!=cfg.team or a.get('user_id')!=cfg.bots[seat]:raise RuntimeError('Unexpected Slack identity')
        self.identity={'team':a.get('team_id'),'user':a.get('user_id')}
    def call(self,method,data):
        if 'channel' in data and data['channel']!=self.cfg.channel:raise RuntimeError('Out-of-instance channel')
        if method=='chat.postMessage' and data.get('channel')!=self.cfg.channel:raise RuntimeError('Posts go to the instance channel only')
        a=self.transport(method,data,self.token)
        if not a.get('ok'):raise RuntimeError('Slack API returned '+str(a.get('error','invalid')))
        return a
    def post(self,text,key):
        return self.call('chat.postMessage',{'channel':self.cfg.channel,'text':text,'unfurl_links':False,'unfurl_media':False,'client_msg_id':str(uuid.uuid5(uuid.NAMESPACE_URL,key))})['ts']

def heard(cfg,name,events):
    """Timestamps this seat should mark with a "heard" reaction: requests it may answer, plus trusted or lead posts that name or mention it."""
    out=[]
    for e in events:
        text=e.get('text','') or ''
        addressed=f"<@{cfg.bots[name]}>" in text or name in routing.named(cfg,text)
        if e.get('reply') or (e.get('authority') and addressed):out.append(e['ts'])
    return out

def process_one(store,name,provider,post,gated=False,react=None):
    cfg=store.cfg
    b=store.claim(name,gated=gated)
    if not b:return False
    if react:
        # Visible receipt (team vocabulary: a seat that heard an addressed message shows it), never a text ACK chorus.
        for ts in heard(cfg,name,b['events']):
            try:react(ts)
            except Exception as exc:print(json.dumps({'reactionError':name,'ts':ts,'errorType':type(exc).__name__}),flush=True)
    try:
        context=read_context(cfg)
        store.set_context(b['id'],context['revision'])
        frame=cfg.seats[name].get('protocol')=='frame'
        request=prompt(cfg,b,context)
        if frame:request=frame_prompt(request,b['id'])
        out=provider(name,request)
        raw,usage=(out['text'],out.get('usage')) if isinstance(out,dict) else (out,None)
        if frame:
            evidence=cfg.dir/'reviewer-responses';evidence.mkdir(mode=0o700,exist_ok=True)
            with (evidence/(b['id']+'.txt')).open('x') as out:
                os.chmod(out.name,0o600);out.write(raw)
        store.respond(b['id'],raw,usage)
        normalized=json.dumps(parse_frame(raw,b['id'])) if frame else raw
        data=parse_result(normalized,b['id'],context['revision'])
        reply=store.complete(b,data)
        if reply:
            # Recheck a mute applied while the provider was running.
            if store.preferences()[name]['mode']=='muted':store.silence(b['id'])
            else:store.posted(b,post(reply,b['id']))
        print(json.dumps({'processed':name,'batch':b['id'],'contextRevision':context['revision'],'events':[e['ts'] for e in b['events']],'publicReply':bool(reply)}),flush=True)
    except Exception as exc:
        store.fail(b['id'],type(exc).__name__+': '+clean(str(exc)))
        print(json.dumps({'failedBatch':b['id'],'provider':name,'errorType':type(exc).__name__}),flush=True)
    return True

def fetch(client,oldest):
    cfg=client.cfg;messages=[];cursor=''
    while True:
        data={'channel':cfg.channel,'oldest':oldest,'limit':100}
        if cursor:data['cursor']=cursor
        page=client.call('conversations.history',data)
        messages.extend(dict(e,team=cfg.team,channel=cfg.channel) for e in page.get('messages',[]))
        cursor=page.get('response_metadata',{}).get('next_cursor','')
        if not cursor:
            if page.get('has_more'):raise RuntimeError('Slack pagination incomplete; cursor not advanced')
            return messages

def poll_once(cfg,store,client,old,heard=None,lookback=None):
    """One pass through the history cursor: reconciliation while the socket is up, intake while it is not, and the catch-up after every (re)connect.
    The read reaches back slack.edit_lookback_seconds (default an hour) so an edit that adds a name still wakes that seat."""
    lookback=cfg.data['slack'].get('edit_lookback_seconds',3600) if lookback is None else lookback
    oldest=min(float(store.cursor(old)),time.time()-lookback)
    messages=fetch(client,f'{oldest:.6f}')
    with ingest_lock(cfg):fresh=store.ingest(messages);edited=store.reconcile(messages)
    (cfg.dir/'watermark.json').write_text(json.dumps({'ts':store.cursor(old)}))
    if heard:heard.submit(fresh+edited)
    return fresh

def starting_watermark(cfg):
    """First start begins at slack.initial_watermark if configured, else the current time (no backlog replay)."""
    p=cfg.dir/'watermark.json';configured=cfg.data['slack'].get('initial_watermark')
    if not p.exists():p.write_text(json.dumps({'ts':configured or f'{time.time():.6f}','createdAt':datetime.now(timezone.utc).isoformat(),'reason':'configured initial watermark' if configured else 'first start; no backlog replay'}))
    return json.loads(p.read_text())['ts']

KNOWN_LIMITS=['thread replies are not ingested; every post is top-level',
    'locked cursor-agent seats (--sandbox enabled) can still write to /tmp',
    'muse headless approval prompts can wait until timeout_seconds and hold the muse queue']
PAUSE_NOTICE={'idle':'Relay paused: no posts from {humans} or the lead for {hours} hours, so agents will not wake. The next post resumes it. No ACK needed.',
    'budget':'Relay paused: the daily limit of {turns} model turns is used up. Agents wake again as the 24-hour window frees up, or when {humans} raises the limit. No ACK needed.'}

def announce_pause(cfg,store,post):
    """Post one top-level notice per pause episode with the lead bot, recorded so intake treats it as context."""
    reason=store.paused()
    if not reason or not store.notice_due(reason):return None
    l=store.limits();text=PAUSE_NOTICE[reason].format(humans=' or '.join(cfg.trusted.values()),hours=l['idle_hours'],turns=l['daily_turns'])
    # Post and record under the ingest lock, so intake never sees the notice before it is known to be one.
    with ingest_lock(cfg):store.record_notice(text,post(text))
    print(json.dumps({'pauseNotice':reason}),flush=True)
    return reason

def health(cfg,store,workers,last_poll,error,intake=None):
    context=read_context(cfg)
    return {'checkedAt':time.time(),'instance':cfg.name,'team':cfg.team,'channel':cfg.channel,'lastSuccessfulPoll':last_poll,'pollError':error,'pid':os.getpid(),'version':3,
        'threadIntake':False,'threadReplies':'unsupported: intake is top-level history only; every post is top-level','contextRevision':context['revision'],'contextPresent':context['present'],
        'posture':{n:{'posture':cfg.posture(n),'tools':cfg.tools(n),'cwd':str(cfg.seat_cwd(n)),'role_policy':cfg.seats[n].get('role_policy')} for n in cfg.workers()},
        'postureWarning':INHERIT_WARNING if any(cfg.posture(n)=='inherit' for n in cfg.workers()) else None,'knownLimits':KNOWN_LIMITS,
        'workers':{t.name:t.is_alive() for t in workers},'gated':[n for n in cfg.workers() if waiting(cfg,n)],'limits':store.limit_status(),'notifications':store.status(),'intake':intake.health() if intake else None}

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--instance',required=True);args=a.parse_args(argv)
    cfg=load(args.instance)
    os.umask(0o077)
    lock=open(cfg.dir/'relay.lock','a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    store=Store(cfg.dir/'deliveries.sqlite',cfg);store.recover();store.mark_started()
    stopped=threading.Event();wake=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:(stopped.set(),wake.set()));signal.signal(signal.SIGINT,lambda *_:(stopped.set(),wake.set()))
    client=Slack(cfg,cfg.poll_seat);client_lead=client if cfg.poll_seat==cfg.lead else Slack(cfg,cfg.lead)
    old=starting_watermark(cfg);ensure_workdirs(cfg)
    providers=Providers(cfg);workers=[]
    def worker(name):
        slack=None
        def post(text,key):
            nonlocal slack
            if slack is None:slack=Slack(cfg,name)
            return slack.post(text,key)
        def react(ts):
            nonlocal slack
            if slack is None:slack=Slack(cfg,name)
            try:slack.call('reactions.add',{'channel':cfg.channel,'timestamp':ts,'name':cfg.data.get('heard_reaction','eyes')})
            except RuntimeError as exc:
                if 'already_reacted' not in str(exc):raise
        while not stopped.is_set():
            try:process_one(store,name,providers.respond,post,waiting(cfg,name),react)
            except Exception as exc:print(json.dumps({'workerError':name,'errorType':type(exc).__name__}),flush=True)
            stopped.wait(5)
    for name in cfg.workers():
        thread=threading.Thread(target=worker,args=(name,),name=name)
        thread.start();workers.append(thread)
    heard=Heard(cfg,store,Slack);heard.start()
    intake=Intake(cfg,store,heard,wake=wake);intake.start()
    print(json.dumps({'ready':True,'version':3,'instance':cfg.name,'channel':cfg.channel,'providers':cfg.workers(),'contextOnly':[n for n in cfg.seats if not cfg.can_reply(n)],'posture':{n:cfg.posture(n) for n in cfg.workers()},'pollSeconds':cfg.poll_seconds,'threadIntake':False,'intake':intake.health()}),flush=True)
    last_poll=None;first=True
    while not stopped.is_set():
        error=None;wake.clear();intake.ensure()
        try:
            # After a restart, look further back for edits made while the relay was down.
            poll_once(cfg,store,client,old,heard,lookback=6*3600 if first else None);first=False
            last_poll=time.time()
            announce_pause(cfg,store,lambda text:client_lead.post(text,'pause:'+text[:40]+str(int(time.time()//3600))))
        except Exception as exc:
            error=type(exc).__name__+': '+clean(str(exc))[:200]
            print(json.dumps({'pollFailure':error}),flush=True)
        temp=cfg.dir/'health.json.tmp';temp.write_text(json.dumps(health(cfg,store,workers,last_poll,error,intake)));temp.replace(cfg.dir/'health.json')
        # Socket connected: reconcile every slack.reconcile_seconds. Otherwise poll every slack.poll_seconds. A hello or close wakes it early.
        wake.wait(intake.interval())
    intake.stop();heard.stop()
    for thread in workers:thread.join()

if __name__=='__main__':main()
