"""Config-driven delivery policy: who receives an event, who may reply, and with what authority."""
import re,sqlite3,time
MODES={'follow_conversation','follow_assigned','mentions_only','muted'}
# Broadcast tokens anywhere, or plain-word group address only at the start of a line ("Everyone, ...", "Y'all: ...").
EVERYONE=re.compile(r"<!(?:channel|here|everyone)(?:\|[^>]*)?>|^\s*[*_>\-•]*\s*(?:hey\s+|hi\s+|ok\s+)?(?:everyone|all of you|y'?all|team|folks)\b",re.I|re.M)
VERBS=r"assess|review|explain|reply|confirm|identify|compare|recommend|summarize|answer|check|tell|show|list|describe|draft|propose|suggest|help|weigh in|thoughts"
OPENERS=r"what|why|how|who|when|where|which|should|can|could|would|will|do|does|did|is|are|any"
FILLER=r"<@\w+>|<!\w+(?:\|[^>]*)?>|everyone|all of you|y'?all|hey|hi|ok|okay|and|team|folks"

def accepted(cfg,event):
    return (event.get('team',cfg.team)==cfg.team and event.get('channel')==cfg.channel
        and event.get('user') in set(cfg.trusted)|set(cfg.bots.values()) and bool(event.get('ts'))
        and event.get('subtype') in (None,'','bot_message','file_share')
        and event.get('thread_ts',event.get('ts'))==event.get('ts'))

def _alias(alias):return r'(?<![\w-])'+re.escape(alias).replace(r'\ ',r'\s+')+r'(?![\w-])'
def named(cfg,text):
    """Seats addressed by plain app name; longest alias wins ("Grok in Cursor" is grok, not cursor)."""
    spans=[];hits={}
    for alias,name in sorted(((a,n) for n,s in cfg.seats.items() for a in s.get('aliases',[])),key=lambda x:-len(x[0])):
        for m in re.finditer(_alias(alias),text,re.I):
            if any(m.start()<e and s<m.end() for s,e in spans):continue
            spans.append((m.start(),m.end()));hits.setdefault(name,m.start())
    return sorted(hits,key=hits.get)

def address(cfg,text):
    """Split a leading address ("Grok and Codex, ...") from the body; only seats named there are being asked."""
    aliases=sorted((a for s in cfg.seats.values() for a in s.get('aliases',[])),key=len,reverse=True)
    text=text.strip();m=re.match(r'(?:\s*(?:'+'|'.join([FILLER]+[_alias(a) for a in aliases])+r')\s*[,:;.!-]*)+',text,re.I)
    return (m.group(0),text[m.end():]) if m else ('',text)

def is_request(cfg,text):
    stripped=address(cfg,text)[1]
    return bool('?' in text or re.search(r'\bplease\b|\b(?:can|could|would|will) (?:you|someone|anyone|y\'?all)\b',text,re.I)
        or re.match(r'(?:'+VERBS+r'|'+OPENERS+r')\b',stripped,re.I))

BULLET=re.compile(r'^\s*(?:[-*\u2022>]+|\d+[.)])?\s*')
IMPERATIVE=VERBS+r"|run|test|fix|write|read|look|investigate|verify|update|add|post|report|take|handle|prepare|audit|try|find|send|share|give|make|start|finish"
def addressed_lines(cfg,text):
    """Seats addressed explicitly at the start of any line. "Codex, classify the links." assigns work whatever the verb.
    After a colon ("- Codex: run the tests.") the rest must ask for something: a roster line ("Codex: Model A") or a verdict ("Codex: PASS confirmed.") is not a request."""
    out=set()
    for line in text.splitlines():
        prefix,body=address(cfg,BULLET.sub('',line).replace('*',''))
        end=prefix.rstrip()[-1:]
        if (end==',' and body.strip()) or (end==':' and (is_request(cfg,body) or re.match(r'(?:'+IMPERATIVE+r')\b',body.strip(),re.I))):out|=set(named(cfg,prefix))
    return out

def plan(cfg,event,prefs):
    """Delivery, reply eligibility and assignment authority are separate. Only trusted humans and the interactive lead start replies."""
    if not accepted(cfg,event):return {}
    text=event.get('text','');sender=event['user']
    human=sender in cfg.trusted
    # The lead's bot is trusted like a human (its posts assign work); relay pause notices are context.
    lead=sender==cfg.bots[cfg.lead] and event.get('lead_origin')=='lead'
    peer=sender in cfg.bots.values() and not lead
    initiator=human or lead
    authority=human or sender==cfg.bots[cfg.lead]
    mentions=[n for n,u in cfg.bots.items() if f'<@{u}>' in text]
    names=named(cfg,text);asked=is_request(cfg,text);everyone=bool(EVERYONE.search(text))
    # A trusted human's top-level post always goes to someone: the seat it names, else the lead. It never sits unread.
    request=asked or human
    lines=addressed_lines(cfg,text) if initiator else set()
    responders=set(mentions)|lines
    if asked and everyone:responders=set(cfg.bots)
    elif lines:pass
    elif request and names:
        prefix=address(cfg,text)[0]
        # A seat mentioned in passing is not asked. The lead must address explicitly ("Grok, ..."); humans fall back to the first name.
        if lead:responders|=set(named(cfg,prefix)) if prefix.rstrip().endswith((',',':')) else set()
        else:responders|=set(named(cfg,prefix) or names[:1])
    elif not mentions and human:  # an untagged human post goes to the lead; an untagged lead post does not wake the lead itself
        owner=[n for n in cfg.bots if prefs.get(n,{}).get('mode')=='follow_assigned' and any(t.lower() in text.lower() for t in prefs.get(n,{}).get('topics',[]) if t)][:1]
        responders=set(owner or [cfg.lead])
    out={}
    for n,u in cfg.bots.items():
        p=prefs.get(n,{});mode=p.get('mode','follow_conversation')
        if mode=='muted' or sender==u:continue
        # An untagged trusted-human request is addressed to whoever routing chose (usually the lead seat), so addressed-only seats still get it.
        direct=n in mentions or n in lines or (initiator and ((asked and everyone) or (request and n in names))) or (human and n in responders)
        relevant=any(t.lower() in text.lower() for t in p.get('topics',[]) if t)
        if mode=='follow_conversation' or direct or (mode=='follow_assigned' and relevant):
            # A teammate's @-mention asks for help, so the mentioned seat may answer it.
            out[n]={'reply':bool(((initiator and n in responders) or (peer and n in mentions)) and cfg.can_reply(n)),'authority':authority,'direct':direct}
    return out

class Ledger:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS deliveries (id TEXT PRIMARY KEY,status TEXT,reply TEXT,slack_ts TEXT,updated REAL)');self.db.commit()
    def claim(self,key):
        c=self.db.execute('INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?,?)',(key,'inflight','','',time.time()));self.db.commit();return bool(c.rowcount)
    def finish(self,key,status,reply='',slack_ts=''):
        self.db.execute('UPDATE deliveries SET status=?,reply=?,slack_ts=?,updated=? WHERE id=?',(status,reply,slack_ts,time.time(),key));self.db.commit()
    def close(self):self.db.close()

def client_response(request,policy='deny'):
    """Unattended ACP client: permission requests are rejected unless the seat's acp_permission allows once."""
    response={'jsonrpc':'2.0','id':request['id']}
    if request['method']=='session/request_permission':
        kinds=('allow_once',) if policy=='allow_once' else ('reject_once','reject_always')
        options=request.get('params',{}).get('options',[])
        chosen=next((o['optionId'] for k in kinds for o in options if o.get('kind')==k),None)
        response['result']={'outcome':{'outcome':'selected','optionId':chosen}} if chosen else {'outcome':{'outcome':'cancelled'}}
    else:response['error']={'code':-32601,'message':'Relay exposes no client tools'}
    return response
