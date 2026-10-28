#!/usr/bin/env python3
"""Offline package checks. No Slack posts, model calls, or provisioning."""
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
errors = []
tracked = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT)
files = sorted({ROOT / name for name in tracked.decode().split('\0') if name and (ROOT / name).is_file()})
required = ['SKILL.md', 'README.md', 'LICENSE', 'agents/openai.yaml',
            'assets/TEAM_CONTEXT.template.md', 'references/listeners.md', 'references/identity.md',
            'references/betkalshi-evidence.md', 'references/workplace-handoff.md',
            'scripts/slack.py', 'tests/test_slack.py']
for name in required:
    if not (ROOT / name).is_file():
        errors.append('Missing file: ' + name)
skill = (ROOT / 'SKILL.md').read_text()
if not re.match(r'^---\nname: slack-agent-team\ndescription: .+\n---\n', skill):
    errors.append('SKILL.md requires name and description frontmatter')
links = 0
for path in files:
    name = str(path.relative_to(ROOT))
    if path.is_symlink():
        errors.append(name + ': unexpected package symlink')
        continue
    content = path.read_text(encoding='utf-8')
    for label, pattern in [
        ('Slack token', r'\bxox[baprs]-[A-Za-z0-9-]{15,}|\bxapp-\d-[A-Za-z0-9-]{15,}|\bxoxe(?:\.xox[bp])?-[A-Za-z0-9-]{15,}'),
        ('GitHub token', r'\bgh[pousr]_[A-Za-z0-9]{25,}|\bgithub_pat_[A-Za-z0-9_]{25,}'),
        ('private path', r'/(?:Users|home)/[a-zA-Z0-9_-]+/'),
        ('private key', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        ('private Slack ID', r'\b[UCTABG]0C[0-9A-Z]{7,9}\b'),
    ]:
        if re.search(pattern, content):
            errors.append(name + ': possible ' + label + ' (value withheld)')
    if path.suffix == '.json':
        try:
            json.loads(content)
        except json.JSONDecodeError:
            errors.append(name + ': invalid JSON')
    if path.suffix == '.md':
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', content):
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            links += 1
            local = (path.parent / unquote(target.split('#')[0])).resolve()
            if not local.is_relative_to(ROOT) or not local.is_file():
                errors.append(name + ': missing/outside local link ' + target)
run = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT,
                     capture_output=True, text=True, timeout=60)
if run.returncode:
    errors.append('Helper tests failed:\n' + run.stderr)
if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'PASS: {len(files)} package files; {links} local links; publication scan.')
print(run.stderr.strip())
print('Live delivery, provider access and workplace proxies require separate evidence.')
