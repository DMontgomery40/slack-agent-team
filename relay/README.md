# Slack relay (reference implementation)

A small Python service that lets a team of coding agents follow one Slack channel and answer when addressed. Each assistant has its own Slack app and bot. Each channel is one *instance*, with its own config, provider sessions, scratch working copies, shared context file, and durable SQLite queue.

Use it when you want several CLI agents (Claude Code, Codex, Cursor Agent, Muse Code, or any ACP-compatible server; Gemini CLI documents a `--acp` mode) to take requests from a shared channel without anyone copying messages by hand. It is a reference implementation for macOS and Linux, not a hosted service. Read it, adapt it, and run it under your own account.

## How it behaves

- **Intake.** One receiver app holds a Socket Mode connection. Each event is stored durably and then acked. History polling runs as reconciliation, and only polling moves the cursor. Without an app-level token or `slack_sdk`, the relay just polls.
- **Waking.** A seat wakes only when it is addressed: an `@mention`, or its name at the start of the message or of a line ("Codex, run the tests."). Untagged requests from a trusted human go to the lead seat. Unaddressed messages are buffered and ride along as context on the seat's next addressed turn.
- **The lead.** The interactive lead (you, in a live agent session) posts with `control.py lead-post`. Those posts are recorded in a lead ledger, which is how the relay tells them apart from its own posts made with the same bot. Each addressed seat adds a 👀 reaction when the message comes in.
- **Limits.** By default 150 model turns per rolling 24 hours, and a pause after 4 hours with no trusted-human or lead post. A one-time notice is posted when the relay pauses.
- **Rules.** Posts are top-level only; the relay never posts in threads. Reply parsing tolerates prose before the JSON.

## Prerequisites

- Python 3.9 or newer. A Codex seat with `"posture": "locked"` needs 3.11+ (`tomllib`); on older Pythons that seat fails closed.
- Optional, for push intake: `python3 -m venv .venv && .venv/bin/pip install slack_sdk==3.45.0`.
- The agent CLIs you want as seats, already signed in under your user account.

## Create an instance

1. Copy this `relay/` directory somewhere outside any repository, for example `~/.config/slack-agent-team/relay`.
2. `mkdir -m 700 instances/<name>` and copy [examples/instance.example.json](examples/instance.example.json) to `instances/<name>/config.json`.
3. Replace every placeholder:
   - workspace, channel and bot user IDs;
   - `owner`, `trusted_humans`, `project` and `source_repo`;
   - for each seat, `model` and `model_label`, and `executable` as an absolute path (`~` is not expanded).

   Delete seats you don't use, or set `"provider": "none"` to keep a seat as context only.
4. Write `instances/<name>/TEAM_CONTEXT.md`. The lead keeps this file current, and every prompt carries it.
5. Choose the wake policy. `default_mode` is `mentions_only` (addressed-only with buffered context) for every new seat. Set it to `follow_conversation` only if you want every seat to wake on every message, at roughly five times the model turns. You can change one seat later with `python3 control.py --instance instances/<name> set <seat> <mode>`.
6. Check the setup:
   - `python3 probe.py --instance instances/<name> --auth --history --prepare`. This makes no posts and prints no tokens.
   - Then send at most one `--seat <seat>` connectivity prompt per seat.

Each worker seat gets a scratch clone of `source_repo` under `instances/<name>/work/<seat>`, with pushes back to the source disabled.

## Slack apps

Create one Slack app per assistant and invite every bot to the channel.

- **Every app** needs the bot scopes `chat:write`, `channels:history` (public channel) or `groups:history` (private channel), `reactions:write` and `users:read`.
- **The receiver app** (the one whose app token is in `slack.app_token_file`) also needs:
  - Socket Mode enabled;
  - an app-level token with `connections:write`;
  - the bot events `message.channels` or `message.groups`.
- **The lead app** also needs `channels:write.invites` or `groups:write.invites`, so it can invite the other seats.

## Token files

Put token files in `slack.credentials_dir` (the example uses `~/.config/slack-agent-team/credentials`):

- one `slack-<seat>.env` per seat, containing `SLACK_BOT_TOKEN=xoxb-...`;
- the receiver's app-level token file, containing `SLACK_APP_TOKEN=xapp-...`.

Each file must be mode 600 and owned by you; the relay refuses any other file. Never commit them, and never put them inside a seat's working copy. A Claude seat with `"posture": "locked"` gets a read-deny rule for this directory.

## Run

To try it in the foreground: `python3 service.py --instance instances/<name>`. Health is written to `instances/<name>/health.json`.

On macOS, use launchd:

1. Copy [launchd/relay.example.plist](launchd/relay.example.plist) to `~/Library/LaunchAgents/`.
2. Replace its placeholders with absolute paths.
3. Load it:

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.slack-agent-team.relay.<name>.plist
launchctl bootout gui/$(id -u)/com.example.slack-agent-team.relay.<name>   # stop
```

On Linux, any supervisor works (for example, a systemd user unit with `Restart=always`).

## control.py

All commands take `--instance instances/<name>`. The instance directory must be owner-only.

| Command | What it does |
| --- | --- |
| `show` | Preferences, queue counts, blocked and active batches |
| `set <seat> <mode> [--topic T]` | `follow_conversation`, `follow_assigned` (with topics), `mentions_only` (addressed-only with buffered context), or `muted` |
| `route --text '...' [--as human\|lead]` | Show which seats would reply, without touching Slack |
| `lead-post [--file F]` | Post top-level as the interactive lead and ledger the message ts (text from a file or stdin) |
| `resolve <batch-id>` | Release a failed or ambiguous batch after you inspect it; never replays it |
| `mark-answered <seat> <ts> [--reply-ts TS]` | The seat already answered elsewhere: deliver the message as context only |

`receipts`, `batch`, `context-read` and `context-ack` are there for inspection and for context-only seats.

## Posture warning

`"posture": "inherit"` is the default. In inherit posture, anything an agent can do interactively it can also do when triggered from Slack: the same settings, permissions, tools and MCP servers. `"posture": "locked"` is opt-in. It pins each CLI to gated permission modes, restricts the shell, and refuses bypass flags. Only trusted humans and the ledgered lead can start replies, but Slack text still reaches the model, so choose posture per seat with that in mind.

## Known limits

- Thread replies are not ingested; intake and posting are top-level only.
- Context rollover is not built yet. Each seat resumes one session per channel indefinitely. Usage is recorded per batch, but nothing moves a seat to a fresh session automatically.
- The fallback from a dropped live socket to polling is verified only by tests with a fake socket, not against a live Slack outage.
- There is no `reactions:read` by default. The relay adds 👀 reactions but cannot see reactions.
- Edits and deletes are ignored. A locked cursor-agent seat can still write to `/tmp`. A Muse approval prompt can hold that seat's queue until `timeout_seconds` runs out.

## Tests

Run these from the repository root: `python3 -m unittest discover -s relay -p 'test_*.py'`. The tests use the example config in a temporary instance directory and fake Slack, socket and provider calls. The test that needs `slack_sdk` is skipped when the SDK is not installed. `python3 scripts/validate.py` runs the same suite.
