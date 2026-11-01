# Slack Agent Team

A skill for reproducing an assistant team that works in Slack. Give the skill to an agent with access to your existing apps, terminal and accounts:

> Read https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/SKILL.md and use it to connect my team. Start from the integrations already working here.

The agent does the setup and asks for missing decisions or access when needed. Existing logins and permission settings remain the starting point.

## What is included

- [The skill](SKILL.md): discover the actual team, connect it, and verify delivery.
- [Receiving messages](references/listeners.md): Monitor setup, fallback checks, direct worker invocation, and known gaps.
- [Slack identities](references/identity.md): apps, bot tokens, channel membership and runtime sessions.
- [Optional team note](assets/TEAM_CONTEXT.template.md): record the project's actual setup in a few lines.
- [A portable helper](scripts/slack.py): `auth`, `history`, `watch`, and top-level `post`, using Python 3.9+ and its standard library.

The portable helper has offline tests and read-only live smoke checks. The package is a skill with small helpers, not a service that hosts or schedules agents.

## Limits that matter

- Claude's interactive Monitor lasts at most 30 minutes and needs re-arming. A missed renewal can leave messages unread.
- The observed watcher reads the last 30 top-level posts and up to 50 entries in qualifying recent threads. It does not paginate, replay all missed history, emit join notices, or guarantee delivery through a long outage. Its output is a 600-character preview; the lead must fetch the full message when needed.
- The computer, session and watcher must be running. Workers launched for one task are not automatically subscribed to later messages.
- Other assistants, vendor bots, Hermes, OpenClaw and OpenRouter-backed agents can participate through their own verified routes. This reference is not evidence that those routes are configured or interoperable.

## Changes from the previous package

The previous version generalized older project choices into requirements: five-minute model heartbeats, listeners for every worker, Jira provisioning, fixed standups, context-window thresholds, and a custom relay. This version removes those defaults and the relay implementation. The earlier package remains available at [commit 252fe08](https://github.com/DMontgomery40/slack-agent-team/tree/252fe08d14af436641ab9057859fb94001ec1c5d). Separately installed copies are unaffected.

Project-specific rules belong to that project's instructions. A working delivery route does not need an additional scheduler, database, model quota, ticket system or approval policy to use this skill.

## Check the package

```sh
python3 scripts/validate.py
```

This runs offline helper tests, checks local links and scans tracked package files for common credential/private-ID patterns. It makes no Slack posts or model calls.

MIT licensed; see [LICENSE](LICENSE). This is an independent community skill.
