# Two kinds of participants: assistants and coding agents

Classify every participant as one of these two kinds before naming, connecting, or assigning it. They behave differently, need different defaults, and are easy to confuse because one vendor often ships both under similar names. Product facts below were checked against official docs on October 18, 2026 (see the [research record](research.md#participant-kinds-october-18-2026)); recheck them, since these products change weekly.

| | **Assistant** (bot, dot, personal assistant, assistant runner) | **Coding agent** |
| --- | --- | --- |
| Examples | ChatGPT dots, Grok Bot, the Claude Slack app (Claude Tag), Muse, Hermes, OpenClaw | Codex (CLI, IDE, cloud tasks), Claude Code, Muse Code, Cursor CLI, Antigravity, Gemini CLI |
| Lives | Hosted by the vendor, or a self-hosted runner, always on | A process on a machine or a cloud worker, started per task or session |
| Memory | Persistent; manages its own context | A session; long sessions roll over at 75–85% of the context window ([coding projects](coding-projects.md)) |
| Slack route | Usually the vendor's own Slack app and triggers (mentions, routines, contact methods) | Usually a relay seat on a custom app, one session per channel; some vendors also launch cloud runs from their Slack app |
| Works on | Personal tasks, research, reminders, accounts the user connected | Repositories, each writer in its own worktree |
| Defaults | [pstack](pstack.md) recommended; private [shared memory](shared-context.md) | [Jira, context rollover, one writer per working copy](coding-projects.md) |

## Same vendor, different product

Treat each pair below as two different participants, never one:

| Assistant | Coding agent | What the docs say |
| --- | --- | --- |
| ChatGPT dots | Codex | One Slack app, `@ChatGPT`, carries both. A dot added to a channel answers its owner when mentioned. `@ChatGPT` can hand repository work to a separate Codex Cloud task. `@Codex` is the legacy name. A Codex CLI session reaches Slack only through a relay seat. [ChatGPT in Slack](https://learn.chatgpt.com/docs/third-party/slack), [dots in Slack](https://learn.chatgpt.com/docs/dots/channels) |
| Grok Bot | Grok in Cursor | Grok Bot has desktop and mobile apps and comes with Cursor plans. Each Team Bot gets its own Slack app and answers mentions and followed threads; untagged messages need a listener routine. Team Bots accept posts from other apps, billed to the owner. A Grok model chosen in Cursor CLI is a different route. [Grok Bot](https://docs.x.ai/grok-bot), [Team Bots](https://docs.x.ai/grok-bot/team-bots) |
| Muse | Muse Code | Muse Wonder Full is available only in Muse Code. Muse is Meta's separate assistant product. [Muse models](https://dev.meta.ai/docs/models) |
| The Claude Slack app (Claude Tag) | Claude Code | Claude Tag reads a channel's top-level messages, and an @-mention guarantees a pickup. The earlier Claude Code in Slack bot answered mentions only and is retired in Tag-connected workspaces. The Claude Code CLI has no first-party Slack route; use a relay seat. [Claude Tag](https://claude.com/docs/claude-tag/overview), [Claude Code in Slack](https://code.claude.com/docs/en/slack) |
| The Cursor Slack app | A Cursor CLI session | `@Cursor` starts a Cloud Agent and reports in that thread. A later `@Cursor` in the same thread adds a follow-up to it, and `@Cursor agent` forces a new one. A CLI session is a separate local process. [Cursor in Slack](https://cursor.com/docs/integrations/slack) |

Hermes and OpenClaw are self-hosted assistant runners with chat gateways that include Slack. OpenClaw can host coding harnesses as plugins; classify each hosted participant by what it actually runs. [OpenClaw](https://github.com/openclaw/openclaw), [Hermes Agent](https://github.com/NousResearch/hermes-agent)

**Slackbot is neither kind.** It is Slack's own built-in assistant, which Slack now describes as a personal agent; admins control who can use it ([Slackbot](https://slack.com/help/articles/202026038-An-introduction-to-Slackbot)). It is not a team member to invite or assign. Relays must filter it by user ID, because Slack reports `is_bot: false` for Slackbot ([user object](https://docs.slack.dev/reference/objects/user-object/)), so a filter that drops bots won't catch it.

When names are ambiguous, identify the participant by product and model, not by its Slack name or its own description. A model that exists only in one product settles which product it is.

## Naming

Name each app for its product, so the kind is visible:
- "Muse" (assistant) and "Muse Code" (coding agent).
- "Grok Bot" and "Grok in Cursor".

Never use a project, device, or model name as the identity. One exception: when two seats run in the same harness and differ only by model, the model is what tells them apart, as with "Grok in Cursor" and "Cursor Composer" (both Cursor CLI). Name them that way, and rename them if the model changes. A project name, such as a 3D printer project or a client name, goes stale when the app joins another channel. A model name goes stale when the model changes. See the [recommended layout](slack-apps-and-agents.md#recommended-layout-one-app-per-assistant-the-channel-is-the-project).

Record the kind in each roster entry (`kind`: `assistant` or `coding-agent`) and in the channel charter's roster, so the lead and every teammate know which rules apply.
