"""The interactive lead is authenticated by this ledger, not by bot identity.
control.py lead-post posts with the lead seat's token and records the returned ts while holding the ingest lock,
so the relay can never ingest a lead post before its ledger entry exists."""
import fcntl,json,os,uuid
from contextlib import contextmanager
from datetime import datetime,timezone

@contextmanager
def ingest_lock(cfg):
    with open(cfg.dir/'ingest.lock','a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)

def ledger_ts(cfg):
    p=cfg.lead_ledger
    if not p.exists():return set()
    return {json.loads(line)['ts'] for line in p.read_text().splitlines() if line.strip()}

def record(cfg,ts,source):
    fd=os.open(cfg.lead_ledger,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        os.write(fd,(json.dumps({'ts':ts,'recorded_at':datetime.now(timezone.utc).isoformat(),'source':source})+'\n').encode());os.fsync(fd)
    finally:os.close(fd)
    os.chmod(cfg.lead_ledger,0o600)

def lead_post(cfg,text,slack=None):
    """Top-level post as the lead seat; the ts is ledgered before the relay's poller can see the message."""
    with ingest_lock(cfg):
        if slack is None:
            from service import Slack
            slack=Slack(cfg,cfg.lead)
        ts=slack.post(text,'lead-post:'+str(uuid.uuid4()))
        record(cfg,ts,'control.py lead-post')
    return ts
