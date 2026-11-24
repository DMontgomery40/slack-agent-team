# Agent Team

A room where you and your coding agents work together, as a desktop app. No Slack.

Claude Code leads, Codex and Muse Code pick up the work, and you talk to all of them in one window. Each room is a plain JSONL file in `~/.agent-team`, and every run is a headless CLI call on your own machine using the logins and permission settings you already have.

## Desktop app

[app/agent-team.html](app/agent-team.html) is a Claude artifact built on the artifact desktop runtime. Open it in the Claude desktop app, choose **Install as app**, and allow access when it asks.

- A message with no @mention goes to the lead. `@codex` or `@muse` wakes just that teammate.
- The lead hands out work by @mentioning a teammate with a brief. When that teammate reports back, the lead is woken to review it.
- Runs show up in the room while they happen: the command being run, the file being edited, elapsed time, a stop button. The prompt, full event log and stderr of every run are kept in `~/.agent-team/runs/`.
- Each agent keeps one session per room (`claude -p --resume`, `codex exec resume`), so a turn only carries what is new since its last one. If a resume fails, the run starts a fresh session with recent history.
- A loop guard pauses after six handoffs in a row (you can change the number), with a Continue button.
- Menu bar item, notifications and a Dock badge when someone posts while the window is in the background.
- Team settings hold the command line for each teammate. Anything with a headless mode can join; plain-text output works for any CLI.

What it does not do: runs are headless, so an agent can't stop and ask you to approve something. Each CLI uses the permissions in its own config (`~/.claude/settings.json`, `~/.codex/config.toml` and so on). Add flags in Team settings to give a teammate more room, for example `--sandbox workspace-write` for Codex, which is read-only by default. The app has to be open for anything to happen: closing the window ends its runs. Muse's default (`muse exec --prompt-file`) follows the command observed in the original setup and is untested here.

The @mention wake-up and loop guard follow [agentchattr](https://github.com/bcurts/agentchattr), which does the same thing for interactive sessions with a local server and tmux. This app uses each CLI's own headless mode instead, so there is no server to run.

```text
~/.agent-team/
  team.json            teammates, rooms, routing settings
  state.json           session ids and what each agent has already seen
  rooms/<room>.jsonl   one message per line: {id, ts, from, kind, text, hop}
  runs/<id>/           prompt.md, events.jsonl, run.json, stderr.txt
```

### From a terminal or another agent

[scripts/team.py](scripts/team.py) reads and posts to the same room files. It has the same shape as the Slack helper, uses only the standard library, and never calls a model.

```sh
python3 scripts/team.py --room general history
echo "@codex can you check the migration?" | python3 scripts/team.py post
python3 scripts/team.py post --as claude < reply.md
python3 -u scripts/team.py watch --state /private-state/lead-seen.txt --self claude
```

The app routes anything appended this way. An interactive Claude Code session can still be the lead: set the lead to "Its own session" in Team and point its Monitor at `team.py watch` instead of the Slack watcher. Monitor's 30-minute limit and the renewal steps in [listeners.md](references/listeners.md) still apply to that route.

## Slack route

The original skill, for a team that already lives in Slack. Give it to an agent with access to your existing apps, terminal and accounts:

> Read https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/SKILL.md and use it to connect my team. Start from the integrations already working here.

The agent does the setup and asks for missing decisions or access when needed. Existing logins and permission settings remain the starting point.

### What is included

- [The skill](SKILL.md): discover the actual team, connect it, and verify delivery.
- [Receiving messages](references/listeners.md): Monitor setup, fallback checks, direct worker invocation, and known gaps.
- [Slack identities](references/identity.md): apps, bot tokens, channel membership and runtime sessions.
- [Optional team note](assets/TEAM_CONTEXT.template.md): record the project's actual setup in a few lines.
- [A portable helper](scripts/slack.py): `auth`, `history`, `watch`, and top-level `post`, using Python 3.9+ and its standard library.

The portable helper has offline tests and read-only live smoke checks. The package is a skill with small helpers, not a service that hosts or schedules agents.

### Limits that matter

- Claude's interactive Monitor lasts at most 30 minutes and needs re-arming. A missed renewal can leave messages unread.
- The observed watcher reads the last 30 top-level posts and up to 50 entries in qualifying recent threads. It does not paginate, replay all missed history, emit join notices, or guarantee delivery through a long outage. Its output is a 600-character preview; the lead must fetch the full message when needed.
- The computer, session and watcher must be running. Workers launched for one task are not automatically subscribed to later messages.
- Other assistants, vendor bots, Hermes, OpenClaw and OpenRouter-backed agents can participate through their own verified routes. This reference is not evidence that those routes are configured or interoperable.

### Changes from the previous package

The previous version generalized older project choices into requirements: five-minute model heartbeats, listeners for every worker, Jira provisioning, fixed standups, context-window thresholds, and a custom relay. This version removes those defaults and the relay implementation. The earlier package remains available at [commit 252fe08](https://github.com/DMontgomery40/slack-agent-team/tree/252fe08d14af436641ab9057859fb94001ec1c5d). Separately installed copies are unaffected.

Project-specific rules belong to that project's instructions. A working delivery route does not need an additional scheduler, database, model quota, ticket system or approval policy to use this skill.

## Check the package

```sh
python3 scripts/validate.py
```

This runs offline helper tests, checks local links and scans tracked package files for common credential/private-ID patterns. It makes no Slack posts or model calls.

MIT licensed; see [LICENSE](LICENSE). This is an independent community skill.
