# Slack Agent Team

A skill for reproducing an assistant team that works in Slack. Give the skill to an agent with access to your existing apps, terminal and accounts:

> Read https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/SKILL.md and use it to connect my team. Start from the integrations already working here.

The agent does the setup and asks for missing decisions or access when needed. Existing logins and permission settings remain the starting point.

## The working reference

The Bet365–Kalshi setup inspected on **28 October 2026** works like this:

1. **Claude Code leads in an interactive session.** Its `Monitor` tool runs a small Python program that reads Slack history about every 20 seconds. New posts enter that same Claude session, including messages with no tag. Empty checks stay in Python and do not invoke a model.
2. **The lead launches Codex and Muse Code for particular tasks.** It passes a brief, a working directory and the existing CLI/model settings. Workers write results and can post to Slack with their own bot tokens. The observed launches are direct CLI delegation; a Slack mention by itself does not start these workers.
3. **The team talks in the main channel.** Short assignments, questions, results and reviews are visible there. The lead integrates the work and answers people.

The lead receives ordinary messages because it has a watcher, not because Slack grants special delivery to a “lead” role. The current watcher sees other bots' posts too, while suppressing its own.

**Welcomes used a different path.** The watcher filters join notices. An older five-minute scheduled history check caught one join; another welcome followed a human request. Those examples do not prove join notifications reach Monitor. See the [dated evidence record](references/betkalshi-evidence.md).

## What is included

- [The skill](SKILL.md): discover the actual team, connect it, and verify delivery.
- [Receiving messages](references/listeners.md): Monitor setup, fallback checks, direct worker invocation, and known gaps.
- [Slack identities](references/identity.md): apps, bot tokens, channel membership and runtime sessions.
- [Workplace handoff](references/workplace-handoff.md): the observed dependencies and decisions for a cloud services team, including API proxies.
- [Optional team note](assets/TEAM_CONTEXT.template.md): record the project's actual setup in a few lines.
- [A portable helper](scripts/slack.py): `auth`, `history`, `watch`, and top-level `post`, using Python 3.9+ and its standard library. Its adaptations from the live scripts are documented in the evidence record.

The portable helper has offline tests and read-only live smoke checks. It has **not** replaced the running BetKalshi watcher. The package is a skill with small helpers, not a service that hosts or schedules agents.

## Limits that matter

- Claude's interactive Monitor lasts at most 30 minutes and needs re-arming. A missed renewal can leave messages unread. The transcript includes such a gap.
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

This runs offline helper tests, checks local links and scans tracked package files for common credential/private-ID patterns. It makes no Slack posts or model calls. It cannot certify a live team or an employer's proxy setup.

MIT licensed; see [LICENSE](LICENSE). This is an independent community skill.
