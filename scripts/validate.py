#!/usr/bin/env python3
"""Offline package checks; does not provision or certify any live integration."""
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []
files = [p for p in ROOT.rglob('*') if p.is_file() and not any(x in {'.git', '__pycache__', '.claude'} for x in p.relative_to(ROOT).parts)]
required = ['SKILL.md', 'README.md', 'LICENSE', 'assets/team.example.json', 'assets/TEAM_CONTEXT.template.md', 'references/lead.md', 'references/team-rules.md',
            'references/listeners.md', 'references/participants.md', 'references/coding-projects.md', 'references/pstack.md',
            'relay/README.md', 'relay/examples/instance.example.json', 'relay/launchd/relay.example.plist']
# Workspace, channel and user IDs from the private deployment this package was derived from. Kept split so this file never matches itself.
PRIVATE_IDS = ['T0C92' + 'NRJM5G', 'C0C9X' + 'D5GJBV', 'U0C8M' + 'GQT3HV']
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
    # Every file, whatever its type: the private deployment's IDs must never ship.
    if any(value in path.read_bytes().decode('utf-8', 'ignore') for value in PRIVATE_IDS):
        errors.append(f'{path.relative_to(ROOT)}: contains a private Slack workspace/channel/user ID; replace it with a placeholder')
    if path.suffix not in {'.md', '.json', '.yaml', '.yml', '.py', '.plist'}:
        continue
    content = path.read_text(encoding="utf-8")
    for label, pattern in [
        ('Slack credential', r'\bxox[baprs]-[A-Za-z0-9-]{15,}'),
        ('Slack app-level credential', r'\bxapp-\d-[A-Za-z0-9-]{15,}'),
        ('Slack rotating credential', r'\bxoxe(?:\.xox[bp])?-[A-Za-z0-9-]{15,}'),
        ('GitHub credential', r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,})'),
        ('private absolute user path', r'/(?:Users|home)/[a-zA-Z0-9_-]+/'),
        ('private key', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        ('real-looking Slack ID', r'\b[UCTABG]0C[0-9A-Z]{7,9}\b'),
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
try:
    team = json.loads((ROOT / 'assets/team.example.json').read_text(encoding='utf-8'))
    if team['lead'] not in team['agents']:
        errors.append('team.example.json: the lead must be one of the agents')
    for name, agent in team['agents'].items():
        if agent.get('kind') not in {'assistant', 'coding-agent'}:
            errors.append(f'team.example.json: {name} needs kind assistant or coding-agent')
except (ValueError, KeyError, OSError) as exc:
    errors.append(f'team.example.json: invalid roster ({type(exc).__name__})')
pin = json.loads((ROOT / 'assets/pstack-source.json').read_text(encoding='utf-8'))['reviewed_commit']
if pin not in (ROOT / 'references/pstack.md').read_text(encoding='utf-8'):
    errors.append('pstack source revision does not match its guide')
# Relay reference implementation: every module compiles and its offline test suite passes (fakes only; no Slack, no provider CLIs).
relay = ROOT / 'relay'
modules = sorted(relay.glob('*.py'))
if not modules:
    errors.append('relay: no Python modules found')
with tempfile.TemporaryDirectory() as tmp:
    for module in modules:
        try:
            py_compile.compile(str(module), cfile=str(Path(tmp) / (module.name + 'c')), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f'relay/{module.name}: does not compile ({exc.exc_type_name})')
try:
    run = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'relay', '-t', 'relay', '-p', 'test_*.py'], cwd=ROOT,
                         env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=600)
    report = run.stderr.strip().splitlines()
    ran = next((line for line in reversed(report) if re.match(r'^Ran \d+ tests? in ', line)), 'no test count reported')
    outcome = report[-1] if report else 'no output'
    if run.returncode:
        errors.append(f'relay tests failed: {ran}; {outcome}\n' + '\n'.join(report[-40:]))
except subprocess.TimeoutExpired:
    ran, outcome = 'timed out', 'FAILED'
    errors.append('relay tests timed out after 600 s')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'PASS: {len(files)} files, {json_count} JSON documents, {links} local links; structure and common publication patterns checked.')
print(f'Relay: {len(modules)} modules compiled; {ran} ({outcome}).')
print('Live Slack routes and provider logins are checked during a real setup, not here.')
