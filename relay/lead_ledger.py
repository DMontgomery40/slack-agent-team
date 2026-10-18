"""Posting as the lead, and the ingest lock shared by polling, Socket Mode and the lead's own posts.
The lead's bot is trusted the way a human is: its posts assign work, whichever process wrote them."""
import fcntl,uuid
from contextlib import contextmanager

@contextmanager
def ingest_lock(cfg):
    with open(cfg.dir/'ingest.lock','a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)

def lead_post(cfg,text,slack=None):
    """Top-level post with the lead seat's token, for a lead session that has no Slack script of its own."""
    if slack is None:
        from service import Slack
        slack=Slack(cfg,cfg.lead)
    return slack.post(text,'lead-post:'+str(uuid.uuid4()))
