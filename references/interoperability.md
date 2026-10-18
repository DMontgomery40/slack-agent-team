# Interoperability: connect the real participant

Read when mixing products, existing sessions, native assistants, or custom bots. Product documentation was reviewed on October 17, 2026; see [research.md](research.md). The route is determined by capabilities, not a logo or model name.

## Discover capabilities separately

| Capability | Evidence |
| --- | --- |
| Read | Can read the intended permitted message/context |
| Receive | New permitted input reaches this participant through its selected route |
| Wake | Idle participant can be activated by the actual human/peer/scheduler |
| Continue | A follow-up reaches the intended existing conversation with required context |
| Reply | Result returns to the intended audience under accurate attribution |
| Act | Requested tool operation completes within configured authority |

Record verified, untested, unsupported, or not applicable plus evidence. Check sender class, public/private channels, DMs, threads, attachments, and schedule behavior separately where relevant. A connector that can post is not automatically a listener. A Slack bot does not automatically accept another bot's messages.

## Select the route

| Route | Use when | Record the boundary |
| --- | --- | --- |
| Native Slack integration | The product supports this account and workflow | Supported sender, account, conversation/task, and follow-up behavior |
| Supported session API/CLI | An installed runtime can address or resume the actual session | Exact session handle, identity, tools, and continuity |
| Desktop-controlled session | The existing app provides the usable path | Verified app/window/chat, foreground control, login/lock/sleep dependencies, interaction owner |
| Connector/MCP only | An active assistant can explicitly read/post with tools | No automatic receive/wake until a separate mechanism is connected |
| Custom app and runner | A maintained adapter can bridge Slack to the selected runtime | Transport, queue/ledger, credentials, session mapping, supervision |
| Manual relay | Automatic/desktop routing remains unavailable | Named human handoff, expected response, and explicit pending automation |

A desktop route can be useful without an API. Inspect live UI, verify focus and recipient before submission, and read back the result and session context. Coordinate ownership of shared foreground interaction so two automations do not type into the wrong window. Prefer supported APIs/CLI for durable unattended operation when available. Screen interaction is not proof the session can be woken while the computer sleeps or locks. If a product requires a human sender, use its supported handoff; do not impersonate one. Desktop input into the target assistant’s own session UI is a desktop relay, not proof of Slack peer activation. Never count a post made through the human’s Slack account as a bot-originated round trip; preserve original actor and relay attribution and mark native peer activation unsupported where appropriate.

Hermes and OpenClaw are possible existing harnesses/runners. Inspect their current instructions, skills, memory boundaries, and configured channels during discovery. Reuse what is already selected; this skill adds no dedicated connection or auto-install for either.

## Product-specific branches

- **ChatGPT dots:** use the dot profile's Slack contact method. Native channel/DM behavior and proactive monitoring are separate. Adding a dot to a channel does not create a monitoring schedule; configure and verify recurring work only when requested. Confirm whose requests it will answer and what private context may be shared. [Dots messaging](https://learn.chatgpt.com/docs/dots/channels).
- **ChatGPT/Codex:** inspect the current `@ChatGPT` Slack route and connected Cloud environment. A new delegated Cloud task is not automatically the local chat the user already has open. Use supported session controls or desktop interaction for that specific chat. [Codex Slack](https://developers.openai.com/codex/integrations/slack).
- **Claude:** distinguish organization Claude Tag from legacy Claude Code in Slack routes; verify current plan and connection. [Claude Tag](https://claude.com/docs/claude-tag/overview), [Claude Code Slack](https://code.claude.com/docs/en/slack).
- **Grok Bot / Cursor:** these products have real shared account and integration infrastructure. Follow [the identity guide](grok-cursor-identity.md) to distinguish an existing personal/Team Bot, a Grok model inside Cursor CLI, a delegated Cursor Cloud Agent, and an independent Cursor session. Preserve parent/worker ownership and verify context transfer; one logo does not mean one runtime, and two logos do not guarantee independent teammates. [Cursor Slack integration](https://cursor.com/docs/integrations/slack).
- **Muse Code or another desktop/terminal assistant:** inspect installed help and current session controls. Preserve the selected product, model, account, and existing session. If the user names a specific model, verify the actual available model ID rather than substituting another provider. A fresh invocation is a new session unless continuity is explicitly supported and verified.
- **Custom model runners/OpenRouter:** a model API supplies inference; the runner supplies tools, memory, sessions, and Slack delivery. Discover exact model IDs/tool support. Configure model fallback and provider routing independently; provider fallback can change execution even when the model ID is unchanged. Record cost, concurrency, and data-processing policy. [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection), [tool calling](https://openrouter.ai/docs/guides/features/tool-calling).

Native capabilities depend on account, plan, installation, and current product behavior. Document a supported constraint and an explicit bridge/manual path where required. Do not promise a universal unattended connection on the strength of an installed skill.
