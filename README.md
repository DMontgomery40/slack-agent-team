# Slack Agent Team

**Assumption: you have authorized your assistant to use your desktop for setup. It should use installed apps, browser, terminal, desktop controls, and connected tools wherever practical, stopping only at real access barriers or actions outside your request.** In practice, it uses the apps and accounts already on your computer to create and configure Slack apps, connect the assistants you already use, and start a small helper service (a relay). You can stop everything at any time; see *Undo* below.

Bring your assistants together in Slack: existing chats and sessions, dots, Grok bots, coding agents, Hermes, OpenClaw, and custom model runners. Use it for day-to-day help, research, household coordination, or a major project. Repositories and coding tools are optional. Hermes and OpenClaw are possible existing tools to discover; mentioning them does not install or connect either product.

This is an open Agent Skill: instructions, setup templates, and acceptance checks. It guides an assistant through connecting real products and proving the connections work. It includes a [reference relay](relay/README.md) that your setup agent configures and runs on your own computer. It is not a hosted service, and it can't make every vendor accept bot messages. Supported native routes, existing desktop sessions, custom adapters, and explicit manual handoffs can coexist.

## Words used here

- **Assistant:** a persistent bot you already use, such as a ChatGPT dot, Grok Bot, the Claude Slack app, Muse, or an OpenClaw "Claw".
- **Coding agent:** a tool that works on code in sessions, such as Codex, Claude Code, Muse Code, Cursor or Antigravity. See [assistants versus coding agents](references/participants.md).
- **Harness:** the program an agent runs in, such as the Codex CLI or Claude Code.
- **Lead:** the one agent in charge of the team.
- **Relay:** a small helper service that reads a Slack channel and hands each message to the coding agents, so they can answer without being tagged.
- **Seat:** one agent's place in a channel, meaning its Slack identity plus its session for that channel.

## Before you start

- A Slack workspace where you can install apps (you're an admin, or app approval is set up).
- The assistants and coding agents you already use, signed in on this computer or in their own apps.
- For coding agents that should follow a channel without tags: this computer awake and logged in, because the relay runs here.
- For coding projects only: the setup agent proposes a Jira board, or reuses your existing tracker. You can say no ([details below](#coding-projects-jira-by-default)).

## Two things for you to do

1. **Point one assistant at this skill.** Paste the message below into whichever assistant or coding agent you already use: a chat window (ChatGPT, Claude, Grok Bot, Muse) or a terminal agent (Claude Code, Codex, Cursor). That one does the setup. The lead you name in step 2 runs the team afterward; it can be the same agent. Or give it [SKILL.md](SKILL.md) directly:

   > Read https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/SKILL.md and use it to connect my assistants. You have desktop access for setup. The lead is: NAME.

2. **Pick a lead.** One assistant has to be in charge, or nothing happens: each one waits for someone else to start. Name the lead in that same message. If you're unsure, pick your strongest coding agent that runs on this computer for a coding project, or your main personal assistant for a personal team. Recommended but not required: give each assistant a role that fits its strengths, or let the lead propose roles ([lead guide](references/lead.md)).

**Everything else here is instructions for agents.** That assistant carries onboarding to the other intended participants through the routes it can actually reach; you do not repeat a setup checklist for each bot. The assistant discovers existing accounts and sessions, installs/loads the skill and its dependencies where supported, configures subscriptions and credentials, reconciles shared context, and verifies real handoffs. It handles both everyday personal help and project coordination. It surfaces only concrete gates it cannot pass, such as your required MFA or an administrator restriction.

Agents: fetch the complete repository tree by Git or [source archive](https://github.com/DMontgomery40/slack-agent-team/archive/refs/heads/main.zip), or resolve linked files against the raw source URL, so references remain accessible. Use the target harness's supported skill location and preserve any existing customized copy. Codex installations using `~/.codex/skills` and Claude Code installations using `~/.claude/skills` can place the whole skill folder in their supported location; discover current harness conventions before installing. Other harnesses use their own supported mechanism. Managed assistants can read the complete required files through connected tools, browser, or authorized desktop delivery. Reading a summary or installing an icon is not setup completion.

## What to expect

- **Untagged replies need a listener.** Adding bots to a channel does not make them read it. Without a running relay or a vendor routine that follows the channel, agents answer only when tagged, or not at all. The setup agent tells you which participants follow the conversation and which only answer mentions.
- **With a relay, agents wake only when addressed.** This package includes a [reference relay](relay/README.md) that your setup agent configures and runs on your computer. Your setup agent configures or builds it, and tells you which of these behaviors you actually have. Name an agent ("Codex, …") or mention it, and it answers. Your untagged questions go to the lead. Everything else is kept as context for each agent's next turn, so a busy channel doesn't wake every model on every message. A 👀 reaction shows who heard you.
- **A relay built to this design can't run forever unnoticed.** By default, at most 150 model turns a day per channel, and a pause after 4 hours with no post from you or the lead. Your next post resumes it.
- **Vendor bots have their own rules.** Some reply only in threads or only to humans. The setup agent records these exceptions instead of hiding them.

## What is included

- A general setup workflow and capability-based interoperability guide, including native dots and desktop-controlled sessions.
- Separate identities for multiple agents using the same model or harness.
- [Grok Bot/Cursor relationships](references/grok-cursor-identity.md): shared accounts, distinct sessions, and delegated workers, plus [Slack APP versus AGENT and token setup](references/slack-apps-and-agents.md).
- A hard line between [assistants and coding agents](references/participants.md). Bots, dots and personal assistants are persistent and vendor-hosted. Coding agents are sessions with repositories. Pairs like Muse and Muse Code, or Grok Bot and Grok in Cursor, are different participants.
- One plainly named Slack app per assistant ("Codex", not "Codex (my-project)"). The channel is the project, and each assistant gets its own session per channel. See [the recommended layout](references/slack-apps-and-agents.md#recommended-layout-one-app-per-assistant-the-channel-is-the-project).
- A [lead charter](references/lead.md): the lead announces itself, stays active in the channel, assigns work by strength, gives shoutouts, and holds weak work accountable.
- No threads by default: everyone posts top-level ([thread policy](references/notifications.md#thread-policy-no-threads-by-default)).
- Agents run the way you run them, including autonomous modes, with their normal tools and MCP servers and no extra approval prompts. Restrictions, such as review-only or a locked-down seat, are opt-in per project.
- A convention for shared context: a project `TEAM_CONTEXT.md` read across `.codex`, `.claude`, and other harness directories, and a separate private `SHARED_MEMORY.md` for personal assistants. Nothing is shared until the setup agent creates the file and every assistant confirms reading the same revision.
- [Coding-project defaults](references/coding-projects.md): Jira as the task tracker, a fresh session at 75–85% of the context window for coding agents, and one writer per working copy.
- [@poteto’s pstack](references/pstack.md) as a recommended (optional) shared skill set for personal assistants, with a pinned official source and a direct-reading fallback across harnesses.
- Generic team, personal-assistant, project, handoff, and channel-charter templates.
- Agent-executed guides for subscribing to all channel messages versus mentions only, with verified switching and mute/catch-up behavior.
- Separate credential lifecycles for one-off projects and persistent personal assistants.
- A [reference relay](relay/README.md): one instance per channel, Socket Mode push intake with polling as backup, addressed-only waking, 👀 receipts, a lead ledger, and daily and idle limits. Python, with offline tests.
- Minimal custom Slack app manifests, delivery/recovery guidance, and evidence-based acceptance checks.
- A dated primary-source research record and [Muse Wonder Full and Opus 5.5 review dispositions](references/final-review.md), and a [Matt Pocock architecture comparison](references/architecture.md).

Use [team.example.json](assets/team.example.json) first. [personal.example.json](assets/personal.example.json) demonstrates a non-coding setup; [project.example.json](assets/project.example.json) adds project workers. Templates are planning records, not configurations that start a service. Replace required values and validate the resulting runtime configuration with the selected product.

Store filled records, logs, credentials, and private identifiers outside this public checkout. Channel visibility and cross-agent sharing remain explicit choices. Product behavior, account eligibility, and APIs can change; the [research record](references/research.md) links the official sources to recheck.

## Cost and undo

- **Cost:** the setup uses the subscriptions and accounts you already have. It adds no new paid service without your approval. Agents answering in Slack use your normal model usage, so a busy channel costs more than a quiet one.
- **Time:** the setup agent pauses for anything only you can do, such as logins, admin approval, or a vendor app's own settings.
- **Undo:** tell your lead "disconnect everything". It stops the relay and any routines it created, removes channel routes, and retires the Slack apps it created. It leaves apps and accounts you already had. See [credentials and lifecycle](references/credentials-and-lifecycle.md).

## Coding projects: Jira by default

For teams that write code, the setup agent connects a Jira board by default (or reuses your existing tracker). Every task becomes a ticket with an owner, scope, acceptance criteria and evidence. This is strongly recommended for this kind of setup. It is also more token-efficient than having every agent reread a pile of shared Markdown or text files to work out who owns what.

To turn it off, say "no Jira" when you point your assistant at the skill, or tell the lead later. Tasks then live in the lead's channel posts and one shared task file. Details are in [coding-projects.md](references/coding-projects.md).

## Agent/maintainer validation

```sh
python3 scripts/validate.py
```

Requires Python 3.9 or newer. This checks package structure, local links, JSON examples, and common accidental credential/private-path patterns. It does not install Slack apps or certify any live team. See [acceptance.md](assets/acceptance.md) for runtime proof.

## Contributing and license

Corrections should include the relevant primary source or a redacted reproduction, update any affected examples, and pass validation. Never include real tokens, workspace/channel IDs, private transcripts, or filled setup records in an issue or pull request.

MIT licensed; see [LICENSE](LICENSE). Product names belong to their respective owners. This is an independent community skill.
