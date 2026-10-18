# Slack Agent Team

**Assumption: you have authorized your assistant to use your desktop for setup. It should use installed apps, browser, terminal, desktop controls, and connected tools wherever practical, stopping only at real access barriers or actions outside your request.**

Bring your assistants together in Slack: existing chats and sessions, dots, Grok bots, coding agents, Hermes, OpenClaw, and custom model runners. Use it for day-to-day help, research, household coordination, or a major project. Repositories and coding tools are optional. Hermes and OpenClaw are possible existing tools to discover; mentioning them does not install or connect either product.

This is an open Agent Skill: instructions, setup templates, and acceptance checks. It guides an assistant through connecting real products and proving the connections work. It does not itself run a relay or make every vendor accept bot messages. Supported native routes, existing desktop sessions, custom adapters, and explicit manual handoffs can coexist.

## One thing for you to do

Point one of your bots, dots, Groks, Claws, or other assistants at [SKILL.md](SKILL.md), or give it this repository URL:

> Read https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/SKILL.md and use it to connect my assistants. You have desktop access for setup.

**Everything else here is instructions for agents.** That assistant carries onboarding to the other intended participants through the routes it can actually reach; you do not repeat a setup checklist for each bot. The assistant discovers existing accounts and sessions, installs/loads the skill and its dependencies where supported, configures subscriptions and credentials, reconciles shared context, and verifies real handoffs. It handles both everyday personal help and project coordination. It surfaces only concrete gates it cannot pass, such as your required MFA or an administrator restriction.

Agents: fetch the complete repository tree by Git or [source archive](https://github.com/DMontgomery40/slack-agent-team/archive/refs/heads/main.zip), or resolve linked files against the raw source URL, so references remain accessible. Use the target harness's supported skill location and preserve any existing customized copy. Codex installations using `~/.codex/skills` and Claude Code installations using `~/.claude/skills` can place the whole skill folder in their supported location; discover current harness conventions before installing. Other harnesses use their own supported mechanism. Managed assistants can read the complete required files through connected tools, browser, or authorized desktop delivery. Reading a summary or installing an icon is not setup completion.

## What is included

- A general setup workflow and capability-based interoperability guide, including native dots and desktop-controlled sessions.
- Separate identities for multiple agents using the same model or harness.
- [Grok Bot/Cursor relationships](references/grok-cursor-identity.md): shared accounts, distinct sessions, and delegated workers, plus [Slack APP versus AGENT and token setup](references/slack-apps-and-agents.md).
- Shared project context across `.codex`, `.claude`, and other harness directories, plus a separate private `SHARED_MEMORY.md` for personal assistants.
- [@poteto’s pstack](references/pstack.md) as shared skill practice for every personal assistant, with a pinned official source and a direct-reading fallback across harnesses.
- Generic team, personal-assistant, project, handoff, and channel-charter templates.
- Agent-executed guides for subscribing to all channel messages versus mentions only, with verified switching and mute/catch-up behavior.
- Separate credential lifecycles for one-off projects and persistent personal assistants.
- Minimal custom Slack app manifests, delivery/recovery guidance, and evidence-based acceptance checks.
- A dated primary-source research record and [Muse Wonder Full and Opus 5.5 review dispositions](references/final-review.md), and a [Matt Pocock architecture comparison](references/architecture.md).

Use [team.example.json](assets/team.example.json) first. [personal.example.json](assets/personal.example.json) demonstrates a non-coding setup; [project.example.json](assets/project.example.json) adds project workers. Templates are planning records, not configurations that start a service. Replace required values and validate the resulting runtime configuration with the selected product.

Store filled records, logs, credentials, and private identifiers outside this public checkout. Channel visibility and cross-agent sharing remain explicit choices. Product behavior, account eligibility, and APIs can change; the [research record](references/research.md) links the official sources to recheck.

## Agent/maintainer validation

```sh
python3 scripts/validate.py
```

Requires Python 3.9 or newer. This checks package structure, local links, JSON examples, and common accidental credential/private-path patterns. It does not install Slack apps or certify any live team. See [acceptance.md](assets/acceptance.md) for runtime proof.

## Contributing and license

Corrections should include the relevant primary source or a redacted reproduction, update any affected examples, and pass validation. Never include real tokens, workspace/channel IDs, private transcripts, or filled setup records in an issue or pull request.

MIT licensed; see [LICENSE](LICENSE). Product names belong to their respective owners. This is an independent community skill.
