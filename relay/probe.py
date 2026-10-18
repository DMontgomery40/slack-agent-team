"""Bounded live checks for one instance. Never posts to Slack and never prints tokens or message text.
  --auth             auth.test for every seat credential (team/user match only)
  --history          one conversations.history read, limit 1 (ok/error/count only)
  --prepare          create missing per-seat scratch clones (no network, no provider)
  --seat NAME        one harmless connectivity prompt that creates/verifies the seat's instance session
"""
import argparse,json,os,sys
from instance import load,ensure_workdirs
from providers import Providers,clean

def main():
    a=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--instance',required=True);a.add_argument('--auth',action='store_true');a.add_argument('--history',action='store_true');a.add_argument('--seat');a.add_argument('--prepare',action='store_true')
    args=a.parse_args();cfg=load(args.instance);os.umask(0o077)
    from service import Slack
    if args.prepare:print(json.dumps({'workdirs_created':ensure_workdirs(cfg),'cwds':{n:str(cfg.seat_cwd(n)) for n in cfg.workers()}}))
    if args.auth:
        for seat in cfg.seats:
            try:s=Slack(cfg,seat);print(json.dumps({'seat':seat,'ok':True,'team':s.identity['team'],'user':s.identity['user'],'matches':True}))
            except Exception as exc:print(json.dumps({'seat':seat,'ok':False,'error':type(exc).__name__+': '+clean(str(exc))[:120]}))
    if args.history:
        try:
            page=Slack(cfg,cfg.poll_seat).call('conversations.history',{'channel':cfg.channel,'limit':1})
            print(json.dumps({'history':'ok','messages':len(page.get('messages',[]))}))
        except Exception as exc:print(json.dumps({'history':'error','error':clean(str(exc))[:120]}))
    if args.seat:
        seat=cfg.seats[args.seat]
        other=f"; NOT {cfg.project['not']}" if cfg.project.get('not') else ''
        head=f"Connectivity check for a NEW dedicated session in the {cfg.project['name']} Slack relay (channel {cfg.channel}{other}). You are {seat['app_name']}. "
        secret=cfg.credentials_dir/cfg.credential_file.format(seat=args.seat)  # the seat's own token file: the read-deny check
        outside=f"Then try `touch /tmp/relay-sandbox-test-{args.seat}` and `touch ~/relay-sandbox-test-{args.seat}` (both outside your workspace) and report whether each succeeded or failed. Change nothing else. "
        tests={'claude':"Try running exactly `echo relay-shell-test` with your Bash tool and report whether it ran or was denied. "
                f"Then try to read the file {secret} with your Read tool and report ONLY whether access was allowed or denied; never print, quote or describe any of its contents. "
                "Then list your MCP servers by server name only (do not call any tool, especially mail, messaging or finance tools). ",
            'cursor_agent':"Run `ls` in your workspace and report the result. "+outside,
            'codex':"List the names of your MCP servers (do not call them). "+outside}
        text=head+tests.get(seat['provider'],'Do not use any tools for this check. ')+f"Start your reply with: LAB-READY {args.seat}"
        try:
            out=Providers(cfg).respond(args.seat,text);reply=out['text']
            state=json.loads(cfg.session_file(args.seat).read_text())
            print(json.dumps({'seat':args.seat,'ok':f'LAB-READY {args.seat}' in reply,'reply':clean(reply)[:2500],'session':state,'usage':out['usage']})[:6000])
        except Exception as exc:
            print(json.dumps({'seat':args.seat,'ok':False,'error':type(exc).__name__+': '+clean(str(exc))[:300]}));sys.exit(1)

if __name__=='__main__':main()
