#!/usr/bin/env python3
"""Local room helper for the Agent Team desktop app.

Reads and appends ~/.agent-team/rooms/<room>.jsonl, the same files the app
uses. No network, no Slack, and it never starts a model.
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

ROOM_ID = re.compile(r'[a-z0-9][a-z0-9_-]{0,39}')
HANDLE = re.compile(r'[a-z0-9][a-z0-9_-]{0,23}')


def base_dir():
    return Path(os.environ.get('AGENT_TEAM_DIR') or Path.home() / '.agent-team')


def room_path(base, room):
    if not ROOM_ID.fullmatch(room):
        raise ValueError('bad_room_name')
    return Path(base) / 'rooms' / f'{room}.jsonl'


def read(path):
    """Every well-formed message in the room, oldest first. Bad lines are skipped."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return []
    out = []
    for line in text.splitlines():
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if isinstance(msg, dict) and isinstance(msg.get('id'), str) and isinstance(msg.get('text'), str):
            out.append(msg)
    return out


def post(path, text, sender=None):
    """Append one message. With sender it posts as that teammate, otherwise as the human."""
    if sender is not None and not HANDLE.fullmatch(sender):
        raise ValueError('bad_handle')
    msg = {'id': uuid.uuid4().hex[:16], 'ts': int(time.time() * 1000),
           'from': sender or 'human', 'kind': 'agent' if sender else 'human', 'text': text, 'hop': 0}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(msg, ensure_ascii=False) + '\n')
    return msg


def render(msg):
    who = msg.get('from', '?')
    who = who if msg.get('kind') == 'human' else '@' + who
    text = ' '.join(msg.get('text', '').split())
    return f"TEAM {msg.get('ts', 0)} {who}: {text}"


def poll(path, state, self_handle=None):
    """One read. The first read seeds the state file; later reads print new messages."""
    first = not state.exists()
    seen = set(state.read_text().split()) if not first else set()
    for msg in read(path):
        if msg['id'] in seen:
            continue
        seen.add(msg['id'])
        if first or msg.get('kind') == 'system' or (self_handle and msg.get('from') == self_handle):
            continue
        print(render(msg), flush=True)
    temp = state.with_name(state.name + '.tmp')
    temp.write_text('\n'.join(sorted(seen)))
    temp.replace(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--room', default=os.environ.get('AGENT_TEAM_ROOM', 'general'), help='room id, as in ~/.agent-team/rooms/<room>.jsonl')
    sub = parser.add_subparsers(dest='command', required=True)
    hist = sub.add_parser('history', help='print the latest messages as JSON')
    hist.add_argument('--limit', type=int, default=30)
    watch = sub.add_parser('watch', help='print new messages, one line each, for a harness such as Claude Monitor')
    watch.add_argument('--state', type=Path, required=True, help='private file that remembers what was printed')
    watch.add_argument('--self', dest='self_handle', help='skip messages posted as this handle')
    watch.add_argument('--interval', type=float, default=2)
    watch.add_argument('--once', action='store_true')
    send = sub.add_parser('post', help='post text read from stdin')
    send.add_argument('--as', dest='sender', help='post as this teammate handle; leave out to post as the human')
    args = parser.parse_args()
    path = room_path(base_dir(), args.room)
    if args.command == 'history':
        print(json.dumps(read(path)[-max(1, args.limit):], ensure_ascii=False))
    elif args.command == 'post':
        text = sys.stdin.read()
        if not text.strip():
            parser.error('provide message text on stdin')
        msg = post(path, text.rstrip('\n'), args.sender)
        print(json.dumps({'ok': True, 'id': msg['id']}))
    else:
        if args.interval <= 0:
            parser.error('--interval must be positive')
        while True:
            poll(path, args.state, args.self_handle)
            if args.once:
                break
            time.sleep(args.interval)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(str(exc) if isinstance(exc, ValueError) else type(exc).__name__, file=sys.stderr)
        sys.exit(1)
