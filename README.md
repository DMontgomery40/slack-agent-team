# Agent Team

A room where you and your coding agents work together, as a desktop app. No Slack.

Claude Code leads, Codex and Muse Code pick up the work, and you talk to all of them in one window. Each room is a plain JSONL file in `~/.agent-team`, and every run is a headless CLI call on your own machine using the logins and permission settings you already have.

## Desktop app

[app/index.html](app/index.html) is a Claude artifact built on the artifact desktop runtime, with the office scene in [app/office/scene.js](app/office/scene.js). Open it in the Claude desktop app, choose **Install as app**, and allow access when it asks.

It's laid out like a team chat: channels and direct messages on the left, the conversation in the middle, and the Office Bot floor on the side. The controls are Mac parts (translucent sidebar, switches, segmented controls, a System Settings style settings sheet), and the window follows light and dark mode.

- A message with no @mention goes to the lead. `@codex` or `@muse` wakes just that teammate, and each teammate has a direct message where everything you send goes to them.
- When the bots hand work to each other you watch it as a group chat: each bot's little character, their replies as bubbles, and a typing bubble with the command it's running. When the last one finishes, the back and forth folds into one line ("4 messages between Claude Code, Codex and Muse Code") and the final answer shows as a normal message marked Summary. Click the line to unfold it.
- The Office pane is Office Bot from [agent-office](https://github.com/deveyn-hainey/agent-office): the same isometric office, characters at desks and status bubbles, driven by the live runs. A working bot shows the command it's on, a bot whose last message asks you something shows as waiting on you, and a failed run shows as stuck. It can fill the window, and the chat avatars are the same characters.
- The lead hands out work by @mentioning a teammate with a brief. When that teammate reports back, the lead is woken to review it.
- The Runs pane has the prompt, every tool call, the exit code and cost for each run; all of it is also kept in `~/.agent-team/runs/`. Search (Cmd+K) looks across every channel.
- Each agent keeps one session per room (`claude -p --resume`, `codex exec resume`), so a turn only carries what is new since its last one. If a resume fails, the run starts a fresh session with recent history.
- A loop guard pauses after six handoffs in a row (you can change the number), with a Continue button.
- Menu bar item, notifications and a Dock badge when someone posts while the window is in the background.
- Settings (Cmd+, or the Settings menu in the menu bar) holds teammates, providers, rooms and routing. Any CLI with a headless mode can join; plain-text output works for all of them.

### Providers

Each teammate picks where its model calls go and who pays:

- **Subscriptions**: each CLI uses the plan you signed in with (Claude Pro or Max, a ChatGPT plan, your Google or Meta account). API keys in your shell are hidden from the run, so they can't quietly switch you to per-token billing.
- **As configured**: nothing is touched; your shell and each CLI's own config decide.
- **Vertex AI / Model Garden**: a project and region, signed in once with `gcloud auth application-default login`. Claude Code gets `CLAUDE_CODE_USE_VERTEX`, Gemini CLI gets `GOOGLE_GENAI_USE_VERTEXAI`, and Codex reaches OpenAI models on Vertex through the Responses API (preview). For open models in Model Garden, put Codex behind LiteLLM.
- **LiteLLM**: one proxy URL and key for the whole team. Claude Code talks to its Anthropic endpoint (`ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`), Codex gets a `model_providers` entry passed with `-c` that points at `/v1/responses`, and Gemini CLI uses `GOOGLE_GEMINI_BASE_URL`. Model names are the `model_name` entries in your LiteLLM config, and Test connection lists them.
- **Anthropic or OpenAI API keys, any other gateway, or a custom environment** for everything else (Bedrock, OpenRouter, a Gemini API key, Muse with `META_API_KEY`).

Keys come from a variable in your login shell, from a command (`op read ...`, `security find-generic-password -w ...`), or are saved in `~/.agent-team/secrets.json` with mode 600. They never go into `team.json` or the run logs, and nothing is written to `~/.claude/settings.json` or `~/.codex/config.toml`: every setting is applied to that one run only. Switching a teammate's provider or model starts it on a fresh session.

What it does not do: runs are headless, so an agent can't stop and ask you to approve something. Each CLI uses the permissions in its own config (`~/.claude/settings.json`, `~/.codex/config.toml` and so on). Add flags in Settings to give a teammate more room, for example `--sandbox workspace-write` for Codex, which is read-only by default. The app has to be open for anything to happen: closing the window ends its runs. The Muse (`muse exec --prompt-file`) and Gemini CLI (`--output-format json`) defaults follow their docs but haven't been run here yet.

The @mention wake-up and loop guard follow [agentchattr](https://github.com/bcurts/agentchattr), which does the same thing for interactive sessions with a local server and tmux. This app uses each CLI's own headless mode instead, so there is no server to run.

```text
~/.agent-team/
  team.json            teammates, providers, rooms, routing settings
  secrets.json         keys you chose to save here (mode 600)
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

The app routes anything appended this way. An interactive Claude Code session can still be the lead: set the lead to "Its own session" in Settings and point its Monitor at `team.py watch` instead of the Slack watcher. Monitor's 30-minute limit and the renewal steps in [listeners.md](references/listeners.md) still apply to that route.

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
