"""Private local control for one relay instance. Never exposed as a worker tool."""
import argparse,json,os,sys
from pathlib import Path
from lead_ledger import lead_post
from instance import load
from notifications import Store
from routing import MODES

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instance',required=True)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('show')
    setp=sub.add_parser('set');setp.add_argument('agent');setp.add_argument('mode',choices=sorted(MODES));setp.add_argument('--topic',action='append')
    receipts=sub.add_parser('receipts');receipts.add_argument('agent');receipts.add_argument('--ts')
    b=sub.add_parser('batch');b.add_argument('id')
    r=sub.add_parser('resolve',help='release a failed/ambiguous batch after inspecting the provider output and Slack; never replays');r.add_argument('id')
    cr=sub.add_parser('context-read',help='claim queued context for a context-only seat');cr.add_argument('agent')
    ack=sub.add_parser('context-ack');ack.add_argument('id')
    rt=sub.add_parser('route',help='show which seats would reply to TEXT (no Slack)');rt.add_argument('--text',required=True);rt.add_argument('--as',dest='sender',choices=['human','lead'],default='lead')
    ma=sub.add_parser('mark-answered',help='seat already answered message TS outside the relay: context only, no reply turn');ma.add_argument('agent');ma.add_argument('ts');ma.add_argument('--reply-ts',default='')
    lp=sub.add_parser('lead-post',help='post top-level as the interactive lead and ledger the ts (text from --file or stdin)');lp.add_argument('--file')
    args=p.parse_args()
    cfg=load(args.instance)
    if getattr(args,'agent',None) and args.agent not in cfg.bots:p.error('Unknown seat for this instance')
    if cfg.dir.stat().st_uid!=os.getuid() or cfg.dir.stat().st_mode&0o077:p.error('Private owner-only instance directory required')
    os.umask(0o077)
    if args.command=='route':
        from routing import plan
        user=next(iter(cfg.trusted)) if args.sender=='human' else cfg.bots[cfg.lead]
        e={'team':cfg.team,'channel':cfg.channel,'user':user,'ts':'1.0','text':args.text,**({'lead_origin':'interactive'} if args.sender=='lead' else {})}
        print(json.dumps({'replies':sorted(n for n,v in plan(cfg,e,{}).items() if v['reply'])}));return
    if args.command=='lead-post':
        text=Path(args.file).read_text() if args.file else sys.stdin.read()
        if not text.strip():p.error('Empty lead post')
        print(json.dumps({'ts':lead_post(cfg,text),'ledger':str(cfg.lead_ledger)}));return
    s=Store(cfg.dir/'deliveries.sqlite',cfg)
    actor='local-uid:'+str(os.getuid())
    if args.command=='set':result=s.preference(args.agent,args.mode,args.topic,actor=actor)
    elif args.command=='receipts':result=[r for r in s.rows(args.agent) if not args.ts or r['ts']==args.ts]
    elif args.command=='batch':result=s.batch(args.id)
    elif args.command=='resolve':s.resolve(args.id,actor);result=s.batch(args.id)
    elif args.command=='mark-answered':s.mark_answered(args.agent,args.ts,args.reply_ts,actor);result=[r for r in s.rows(args.agent) if r['ts']==args.ts]
    elif args.command=='context-read':
        if cfg.can_reply(args.agent):p.error('Seat has a provider worker; its queue is not read by hand')
        result=s.claim(args.agent)
    elif args.command=='context-ack':
        b=s.batch(args.id)
        if cfg.can_reply(b['name']) or b['status']!='processing':p.error('Expected an active context-only receipt')
        s.complete({'id':b['id'],'name':b['name'],'events':[]},{'receipt':b['id'],'reply':None,'memory':'Read by hand'})
        result=s.batch(args.id)
    else:result=s.status()
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
