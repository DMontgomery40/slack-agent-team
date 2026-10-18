"""Shared team context (written by the lead) injected into every provider prompt with its revision."""
import hashlib

def read_context(cfg):
    p=cfg.context_path
    raw=p.read_bytes() if p.exists() else b''
    digest=hashlib.sha256(raw).hexdigest();text=raw.decode('utf-8','replace')
    return {'revision':'sha256:'+digest[:16],'sha256':digest,'present':p.exists(),
        'truncated':len(text)>cfg.context_max_chars,'text':text[:cfg.context_max_chars]}

def same_revision(echoed,revision):
    value=str(echoed).strip().lower()
    return value in (revision,revision.split(':',1)[1])
