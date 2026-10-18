#!/usr/bin/env python3
"""Offline package checks; does not provision or certify any live integration."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []
files = [p for p in ROOT.rglob('*') if p.is_file() and not any(x in {'.git', '__pycache__'} for x in p.relative_to(ROOT).parts)]
required = ['SKILL.md', 'README.md', 'LICENSE', 'assets/team.example.json', 'assets/personal.example.json', 'references/notifications.md', 'references/credentials-and-lifecycle.md', 'references/shared-context.md', 'references/pstack.md']
for name in required:
    if not (ROOT / name).is_file():
        errors.append(f'Missing required file: {name}')
text = (ROOT / 'SKILL.md').read_text(encoding="utf-8")
front = re.match(r'^---\n(.*?)\n---\n', text, re.S)
if not front or not re.search(r'^name: slack-agent-team$', front[1], re.M) or not re.search(r'^description: .+', front[1], re.M):
    errors.append('SKILL.md requires the expected name and a nonempty description')
links = 0
json_count = 0
for path in files:
    if path.is_symlink():
        errors.append(f'Package symlink requires review: {path.relative_to(ROOT)}')
    if path.suffix not in {'.md', '.json', '.yaml', '.yml', '.py'}:
        continue
    content = path.read_text(encoding="utf-8")
    for label, pattern in [
        ('Slack credential', r'\bxox[baprs]-[A-Za-z0-9-]{15,}'),
        ('GitHub credential', r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,})'),
        ('private absolute user path', r'/(?:Users|home)/[a-zA-Z0-9_-]+/'),
        ('private key', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    ]:
        if re.search(pattern, content):
            errors.append(f'{path.relative_to(ROOT)}: possible {label}; inspect without printing its value')
    if path.suffix == '.json':
        try:
            json.loads(content)
            json_count += 1
        except json.JSONDecodeError as exc:
            errors.append(f'{path.relative_to(ROOT)}: invalid JSON at line {exc.lineno}')
    if path.suffix == '.md':
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', content):
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            links += 1
            local = (path.parent / unquote(target.split('#')[0])).resolve()
            if not local.is_relative_to(ROOT) or not local.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing/outside local link {target}')
for name in ['team.example.json', 'personal.example.json', 'project.example.json']:
    try:
        data = json.loads((ROOT / 'assets' / name).read_text(encoding="utf-8"))
        agents = data['agents']
        ids = [a['id'] for a in agents]
        if len(ids) != len(set(ids)):
            errors.append(f'{name}: duplicate participant IDs')
        subscription_shape = set(json.loads((ROOT / 'assets/subscription.example.json').read_text(encoding='utf-8')))
        credential_shape = set(json.loads((ROOT / 'assets/credentials.example.json').read_text(encoding='utf-8'))['credentials'][0])
        for a in agents:
            if 'notification_mode' in a['slack'] or 'notification_preferences' in a['slack']:
                errors.append(f'{name}: legacy notification shape for {a["id"]}')
            for subscription in a['subscriptions']:
                if set(subscription) != subscription_shape or subscription['participant_id'] != a['id']:
                    errors.append(f'{name}: inconsistent subscription shape/recipient for {a["id"]}')
            for credential in a['credentials']:
                if set(credential) != credential_shape or a['id'] not in credential['participant_ids']:
                    errors.append(f'{name}: inconsistent credential shape/owner for {a["id"]}')
            if set(a['capabilities']) != {'read', 'receive', 'wake', 'continue', 'reply', 'act'}:
                errors.append(f'{name}: incomplete capability card for {a["id"]}')
        if name == 'personal.example.json' and data['repository'] is not None:
            errors.append('Personal example must remain usable without a repository')
    except (ValueError, KeyError, OSError) as exc:
        errors.append(f'{name}: invalid planning structure ({type(exc).__name__})')
pin = json.loads((ROOT / 'assets/pstack-source.json').read_text(encoding='utf-8'))['reviewed_commit']
if pin not in (ROOT / 'references/pstack.md').read_text(encoding='utf-8'):
    errors.append('pstack source revision does not match its guide')
project = json.loads((ROOT / 'assets/project.example.json').read_text(encoding='utf-8'))
for harness in ['.codex', '.claude', '.cursor', '.muse', '.agents', '.gemini', '.grok', '.hermes', '.openclaw']:
    if harness not in project['context']['harness_directories']:
        errors.append(f'Project context inventory missing {harness}')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'PASS: {len(files)} files, {json_count} JSON documents, {links} local links; structure and common publication patterns checked.')
print('Live routing, provider compatibility, credentials and Slack installation remain setup-time acceptance checks.')
