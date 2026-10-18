# Slack Agent Team

**Assumption: you have authorized your assistant to use your desktop for setup. It uses the apps, browser, terminal and accounts already on your computer, and stops only at real access barriers, such as a login only you can do.**

Your assistants and coding agents, working as one team in a Slack channel. A lead assigns the work, follows it up and keeps you in the loop. Everyone else picks up their part, reports back and asks each other for help in the open.

This skill copies setups that have run real projects for days at a time:
- one Slack app per assistant;
- a lead that checks the channel every five minutes;
- tickets, claims and one owner per task;
- a short shared vocabulary.

It doesn't invent rules those setups didn't need.

## Two things for you to do

1. **Point one assistant at this skill.** Paste this into any assistant or coding agent you already use, such as ChatGPT, Claude, Grok Bot, Muse, Claude Code, Codex or Cursor. That one does the setup:

   > Read https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/SKILL.md and use it to connect my assistants. You have desktop access for setup. The lead is: NAME.

2. **Pick a lead.** One agent has to be in charge, or nothing happens: each one waits for someone else to start.
   - For a coding project, pick your strongest coding agent on this computer.
   - For a personal team, pick your main personal assistant.

   Optionally give each agent a role that fits its strengths, or let the lead propose roles.

Everything else is done by the agents. They find your assistants, show you the list ("tell me who to add or leave out"), create or reuse the Slack apps, invite everyone and set up how each one hears the channel. Then they start work. They come back to you only for things only you can do, like a login or an approval.

## What you get

- **One plainly named Slack app per assistant:** "Codex", "Claude Code", "Muse Code", never "Codex (my-project)". The channel is the project. Each assistant gets its own session per channel.
- **A lead that runs the team.**
  - It announces itself.
  - It checks the channel every five minutes and assigns work by name.
  - It follows up on READY, BLOCKED and DONE.
  - It gives shoutouts for good work and calls out weak work with evidence.
  - It asks you only for what only you can give.
- **Every agent listens on its own:**
  - Codex runs a heartbeat;
  - Claude Code runs a loop;
  - agents that can't keep a session open get a small bridge or relay.
- **Team rules from long runs:**
  - one owner per ticket and per file area;
  - claim before editing;
  - one active task per agent;
  - raise blockers within five minutes;
  - a short hourly standup during active work;
  - tag the agents you need, and tag the human only for decisions, logins or approvals;
  - post top-level, not in threads.
- **Coding projects:** Jira by default, and a fresh session when a coding agent's context window is 75–85% full.
- **Every coding agent writes code,** the way you run it, including autonomous (yolo) modes, with its normal tools and MCP servers. Each one works on its own copy and branch, and the lead integrates. The lead doesn't do the work it has assigned to someone else. Restrictions are opt-in per agent.
- **A clear line between assistants and coding agents.** Bots, dots and personal assistants are a different kind of participant from coding agents, even when one vendor ships both under similar names.
- **Personal-assistant teams:** [@poteto's pstack](references/pstack.md) is recommended as a shared skill set, but it's optional.

## Why this instead of Agent Tincan or Reason Network

[Agent Tincan](https://github.com/mvanhorn/agent-tincan) and [Reason Network](https://github.com/reason-machines/reason-network) are good at one thing: carrying a message from one agent to another. This skill gives your agents a team: a lead, owners, tickets, and a channel where you can watch and step in. The comparison below is based on both projects' READMEs as of October 18, 2026.

| | Slack Agent Team | Agent Tincan | Reason Network |
| --- | --- | --- | --- |
| Where the work happens | Your Slack channel, top-level posts that you and your teammates read | Requests and replies through a relay on your Tailscale network | Messages between agent sessions, peer to peer across teammates' computers |
| What you add | Slack apps, plus listeners on the computer you already use | A Tailscale network and an always-on machine for the relay | A background daemon on every computer, optionally a Reason account |
| Who runs the work | A named lead that assigns, follows up and holds work to account | Nobody; any agent asks any other | Nobody; any agent messages any other |
| How work is tracked | Tickets, claims, one owner per scope, status words everyone reads | Request and reply chains, plus a trace command | Each session's title and todo list |
| Where scope comes from | You or the lead; peers help, but don't hand out new scope | "A request from a joined agent is acted on as if you asked" | Team members; `ask_user` pop-ups for sign-off |
| Bots already in your Slack | ChatGPT dots, Grok Bot, Claude, Cursor join as teammates | Their own adapters, outside Slack | Coding agents, not Slack bots |

What that means in practice:

- **A team, not a pipe.** Passing messages between agents leaves you as the project manager. Here the lead does that job:
  - it breaks the work into tickets and gives each one an owner;
  - it chases blockers;
  - it checks evidence before calling anything done;
  - it tells you when something is wrong.
- **You see everything.** Every assignment, claim, review and result is a post in a channel you already read, and you can step in at any point. With message pipes, agent-to-agent traffic happens out of view unless you go looking for it.
- **No new network, server or account.** You keep the Slack workspace, the computer and the subscriptions you already have. Agents that run locally need this computer awake.
- **The bots you already have join in.** ChatGPT dots, Grok Bot, the Claude app and Cursor work in the same channel next to your coding agents.
- **Built from long runs, not a demo.** The rules here are the ones that kept multi-agent projects moving for days: claim before you edit, one active task each, blockers within five minutes, done means observed evidence.

If your agents can't share a Slack workspace, those tools are a good pipe. This skill is the team.

## What to expect

- **An agent hears the channel only if something delivers messages to it.** Adding a bot to a channel isn't enough. The setup agent gives each participant a listener and tells you which ones follow the conversation and which only answer when named.
- **The lead checks in every five minutes** while its app or terminal session is open, so an untagged question can take up to five minutes to get an answer. Local agents need this computer awake and logged in.
- **With the reference relay,** agents wake when you name them with a request ("Codex, run the tests") or @-mention them. A 👀 reaction shows who heard you. By default the relay stops at 150 model turns a day per channel, and pauses after 4 hours with no post from you or the lead.
- **Vendor bots have their own rules.** For example, some only answer in threads. The lead re-posts their results top-level.
- **Slack shows each assistant as one app.** The per-channel "agent" is the session behind it, and Slack has no per-session badge. Slack's AGENT badge is an optional, app-wide setting.

## Cost and undo

- **Cost:** it uses the subscriptions and accounts you already have, and adds no paid service without your approval. A busy channel uses more model turns than a quiet one. A five-minute lead heartbeat is one lead turn every five minutes while it runs.
- **Undo:** tell the lead "disconnect everything". It:
  - stops the listeners and heartbeats it started;
  - removes what it added to channels;
  - retires the Slack apps it created;
  - leaves your existing apps and accounts alone.

  It also saves a copy-paste undo script during setup.

## Coding projects: Jira by default

For teams that write code, the setup agent connects a Jira board, or reuses your existing tracker. Every task becomes a ticket with an owner, scope, acceptance criteria and evidence. That costs fewer tokens than every agent rereading a pile of shared Markdown files to work out who owns what.

To turn it off, say "no Jira" when you point your assistant at the skill, or tell the lead later. Tasks then live in the lead's channel posts and one shared task file. Details are in [coding-projects.md](references/coding-projects.md).

## For maintainers

```sh
python3 scripts/validate.py
```

This checks package structure, local links, JSON examples, and common accidental credential or private-ID patterns. It doesn't install anything or certify a live team.

Never include real tokens, workspace or channel IDs, private transcripts, or filled setup records in an issue or pull request. MIT licensed; see [LICENSE](LICENSE). Product names belong to their owners. This is an independent community skill.
