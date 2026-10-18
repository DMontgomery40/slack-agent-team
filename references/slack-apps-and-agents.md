# Slack apps, agents, and tokens

Read when creating credentials, diagnosing an APP/AGENT label, or selecting Slack's Agent messaging experience. These are related configuration layers, not interchangeable entities.

## Recommended layout: one app per assistant; the channel is the project

- **One Slack app per assistant, named for the assistant only:** "Codex", "Claude Code", "Muse Code". Never put a project name in an app's name. The app shows the same name in every channel it joins, so a project-named app becomes misleading the moment it helps somewhere else.
- **Each channel is a project or purpose.** Each assistant gets its own session per channel, run by its own loop or a relay. That per-channel session is the "agent for that channel". Slack doesn't host it, and Slack has no per-session badge, so every channel shows the same app. One bot token serves all of that assistant's channels.
- **Slack's APP/AGENT badge is unrelated.** It is a display and feature setting, described below. It does not create per-channel identities or tokens.
- **Use a separate app only for a concrete reason:**
  - Two seats from the same assistant speak in the same channel and need separate identities. Name them by role, for example "Claude Code · PM". If they share one identity instead, prefix every post with the role, for example `[PM]`.
  - The seats need different scopes.
  - You need to contain damage: a bot token can read every channel its bot has joined, so a project that must be sealed off gets its own app, or its own workspace.
  - It has a different owner or a different retirement plan.
  - It is in a different workspace, which needs its own installation anyway.
- **Vendor apps** (Cursor, Claude, ChatGPT, Grok Bot) already come as one app per vendor or per bot. Use their own channel and project settings.
- **Retire duplicates.** If a workspace already has several apps for the same assistant, often one per earlier project, keep one, rename it plainly, and move every service and helper that uses the others onto its token. Then retire the extras: `auth.revoke` with an extra app's own bot token deactivates that bot and removes it from every channel ([auth.revoke](https://docs.slack.dev/reference/methods/auth.revoke/)), and Manage apps can remove the app entirely. Identify duplicates by product and model, not by name; for example, a model that exists only in one CLI tells you which product the seat really is. Two apps showing the same name is worse than one awkward name.
- **Per-message names are cosmetic.** With `chat:write.customize` an app can post under a different name or icon per message, for example "Codex · client-x". It is still the same bot, mentions still go to the app, and Slack asks that this be used sparingly and clearly signposted. It is not a substitute for the layout above. [chat.postMessage](https://docs.slack.dev/reference/methods/chat.postMessage/).
- **Renaming an existing app:** change `display_information.name` and `features.bot_user.display_name` in its manifest. With unchanged scopes no reinstall is needed, and the bot user ID and token stay the same. In an October 2026 test, the internal @handle chosen at first install did not change; messages and mentions show the display name.
- **Adding scopes** requires a reinstall. In the same test, the existing non-rotating bot token kept working and gained the new scope. Verify with the `x-oauth-scopes` header returned by `auth.test`; do not assume either outcome.
- **The manifest field `settings.is_mcp_enabled`** controls the app's use of Slack's own MCP server. It does not control the MCP servers your agents use; those belong to each harness.

| Layer | Meaning and verification |
| --- | --- |
| Slack app | Configuration container: app ID, features, OAuth scopes, subscriptions, installation/distribution |
| Installed bot user | The identity users mention and see posting; resolve its `U…` user ID separately from its `B…` bot ID |
| Workspace installation | Authorization in a particular workspace, with its actual grants and credential lifecycle |
| Bot OAuth token (`xoxb-`) | Authorizes supported bot Web API operations for that installation; not scoped merely by a channel name |
| App-level token (`xapp-`) | Used with `connections:write` for Socket Mode; does not replace the bot token for ordinary posting/history |
| Agent/Assistant feature | Slack-native interaction surfaces, labeling and associated methods/events; inspect the app's actual configuration |
| Runtime/session | The model, tools, memory and receiver doing the work; an AGENT label does not start it |

Slack does not introduce a distinct “agent token” just because a bot is displayed as AGENT. The current Agent experience uses `features.agent_view`; older Assistant configurations use `assistant_view`. `assistant:write` enables supported agent features, including agent labeling. These features are more than a cosmetic badge, but do not grant channel-history access or subscribe a runtime to every message. [Developing an agent](https://docs.slack.dev/ai/developing-agents/), [token types](https://docs.slack.dev/authentication/tokens/).

## Configure the requested experience

1. Determine whether the workflow needs ordinary channel communication or Slack's native Agent experience. Existing channel bots can communicate without migrating their UI. Inspect the app ID and ownership, current manifest/features, grants, and receiving runtime; preserve vendor-managed configuration through its supported controls.
2. If Agent experience is required and the app is operator-managed, use the actual app settings. Current Slack UI may call this **Agents & AI Apps → Agent App**; installed versions have also exposed **Agents → Mark this app as an agent app**. Verify the visible control rather than searching for a new token type.
3. Check Slack's current migration contract before applying it. The documented `assistant_view` → `agent_view` migration is one-way. Inspect the current UI transition even when enabling Agent mode on an ordinary app for the first time; do not assume that toggle is reversible. Perform the change only when covered by the requested native Agent experience, never merely to repair message delivery or make icons match. Configure its required scope, supported events, and runtime handlers together: the new experience changes startup, status/title, and cancellation handling. `agent_view.agent_description` is required. Marketplace apps may require review; some agent features depend on plan eligibility. [Official migration](https://docs.slack.dev/ai/migrating-to-agent-messaging/), [manifest reference](https://docs.slack.dev/reference/app-manifest/).
4. Complete any required reinstall/reauthorization through authorized tools/UI. Re-read actual grants and identity; do not assume the old token survives, changes, or must be replaced based on a previous installation. Store any changed credential securely under its existing ownership reference. Refresh Slack if its displayed experience is stale.
5. Verify the selected UI experience and a real receive/process/reply cycle separately. `users.info` bot status is not proof of the displayed APP/AGENT label. Test channel, DM and thread behavior on the surfaces requested.

**Done:** app feature, granted credential, visible identity and working runtime have separate evidence. If the existing app is vendor-managed, record the supported vendor flow instead of editing its manifest yourself.

For temporary versus persistent ownership, follow [credentials-and-lifecycle.md](credentials-and-lifecycle.md). The [minimal custom manifests](../assets/README.md) intentionally provide ordinary channel transport; they are not complete Slack Agent-experience implementations.

Inspect the installed SDK before choosing handler helpers; no universal `app.agent()` registration API is assumed. [Slack Code](https://docs.slack.dev/ai/slack-code/) channels are an optional additional feature, not a prerequisite for ordinary channel intake.
