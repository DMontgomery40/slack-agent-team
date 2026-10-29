#!/usr/bin/env python3
"""Portable version of BetKalshi's history watcher and top-level post helper.

Uses only Slack Web API calls. It neither starts nor invokes a model.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import warnings
from pathlib import Path


class SlackError(RuntimeError):
    def __init__(self, code, retry_after=0):
        super().__init__(code)
        self.retry_after = retry_after


class Slack:
    def __init__(self, token, channel):
        self.token = token
        self.channel = channel

    def call(self, method, **args):
        url = 'https://slack.com/api/' + method
        headers = {'Authorization': 'Bearer ' + self.token}
        data = None
        if method == 'chat.postMessage':
            headers['Content-Type'] = 'application/json; charset=utf-8'
            data = json.dumps(args).encode()
        else:
            url += '?' + urllib.parse.urlencode(args)
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            retry = int(exc.headers.get('Retry-After', '0')) if exc.code == 429 else 0
            raise SlackError('http_' + str(exc.code), retry) from None
        if not result.get('ok'):
            code = result.get('error', 'slack_error')
            raise SlackError(code if re.fullmatch(r'[a-z_]+', str(code)) else 'slack_error')
        return result

    def post(self, text):
        return self.call('chat.postMessage', channel=self.channel, text=text,
                         unfurl_links=False, unfurl_media=False)


def poll(api, channel, self_id, state, names, now=None):
    """One read; first read seeds history, subsequent reads print new previews."""
    now = time.time() if now is None else now
    first = not state.exists()
    seen = set(state.read_text().split()) if state.exists() else set()
    messages = api('conversations.history', channel=channel, limit=30)['messages']
    batch = []
    retry_after = 0
    for message in messages:
        batch.append(message)
        if not retry_after and message.get('reply_count') and float(message.get('latest_reply', '0')) > now - 7200:
            try:
                replies = api('conversations.replies', channel=channel, ts=message['ts'], limit=50)
                batch.extend(replies['messages'][1:])
            except (SlackError, OSError, ValueError, KeyError) as exc:
                retry_after = getattr(exc, 'retry_after', 0)
                if not retry_after:
                    code = str(exc) if isinstance(exc, SlackError) else type(exc).__name__
                    warnings.warn('Slack thread read failed: ' + code)
    for message in sorted(batch, key=lambda m: float(m['ts'])):
        ts = message['ts']
        if ts in seen:
            continue
        seen.add(ts)
        if first or message.get('user') == self_id or message.get('subtype') in ('channel_join', 'bot_add'):
            continue
        user = message.get('user') or message.get('bot_id', '?')
        if user not in names and not retry_after:
            try:
                profile = api('users.info', user=user)['user']
                names[user] = profile.get('real_name') or profile.get('name') or user
            except (SlackError, OSError, ValueError, KeyError) as exc:
                retry_after = max(retry_after, getattr(exc, 'retry_after', 0))
                if not retry_after:
                    names[user] = user
        text = ' '.join(message.get('text', '').split())[:600]
        thread = message.get('thread_ts')
        where = f' (thread {thread})' if thread and thread != ts else ''
        print(f'SLACK {ts}{where} {names.get(user, user)} [{user}]: {text}', flush=True)
    temp = state.with_name(state.name + '.tmp')
    temp.write_text('\n'.join(sorted(seen, key=float)))
    temp.replace(state)
    if retry_after:
        raise SlackError('http_429', retry_after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--token-env', default='SLACK_BOT_TOKEN', help='environment variable holding this bot token')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('auth', help='read and print bot identity without posting')
    sub.add_parser('history', help='read the latest 30 top-level posts, including join notices')
    watch = sub.add_parser('watch', help='print new messages for a harness such as Claude Monitor')
    watch.add_argument('--state', type=Path, required=True, help='existing private directory; one state file per watcher')
    watch.add_argument('--interval', type=float, default=20)
    watch.add_argument('--once', action='store_true', help='read once, update local state and exit')
    sub.add_parser('post', help='post text read from stdin as this bot, top-level')
    args = parser.parse_args()
    token = os.environ.get(args.token_env)
    channel = os.environ.get('SLACK_CHANNEL_ID', '')
    if not token:
        parser.error(f'set {args.token_env} in the environment')
    if args.command != 'auth' and not channel:
        parser.error('set SLACK_CHANNEL_ID in the environment')
    if args.command == 'watch' and args.interval <= 0:
        parser.error('--interval must be positive')
    slack = Slack(token, channel)
    identity = slack.call('auth.test')
    if args.command == 'auth':
        print(json.dumps({key: identity.get(key) for key in ('team_id', 'user_id', 'bot_id', 'user')}))
    elif args.command == 'history':
        print(json.dumps(slack.call('conversations.history', channel=channel, limit=30)['messages']))
    elif args.command == 'post':
        text = sys.stdin.read()
        if not text.strip():
            parser.error('provide message text on stdin')
        result = slack.post(text)
        print(json.dumps({'ok': True, 'ts': result['ts']}))
    else:
        names = {}
        while True:
            delay = args.interval
            try:
                poll(slack.call, channel, identity['user_id'], args.state, names)
            except (SlackError, OSError, ValueError, KeyError) as exc:
                if args.once:
                    raise
                code = str(exc) if isinstance(exc, SlackError) else type(exc).__name__
                print('SLACK-WATCH-ERROR ' + code, flush=True)
                delay = max(delay, getattr(exc, 'retry_after', 0))
            if args.once:
                break
            time.sleep(delay)


if __name__ == '__main__':
    try:
        main()
    except (SlackError, OSError, ValueError, KeyError) as exc:
        print(str(exc) if isinstance(exc, SlackError) else type(exc).__name__, file=sys.stderr)
        sys.exit(1)
