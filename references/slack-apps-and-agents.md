# Slack apps, agents, and tokens

Read when creating credentials, diagnosing an APP/AGENT label, or selecting Slack's Agent messaging experience. These are related configuration layers, not interchangeable entities.

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
5. Verify the selected UI experience and a real receive/process/reply cycle separately. `users.info` bot status is not proof of the displayed APP/AGENT label. Test channel, DM and thread behavior on the surfaces requested; configure all-versus-mentions through [notifications.md](notifications.md).

**Done:** app feature, granted credential, visible identity and working runtime have separate evidence. If the existing app is vendor-managed, record the supported vendor flow instead of editing its manifest yourself.

For temporary versus persistent ownership, follow [credentials-and-lifecycle.md](credentials-and-lifecycle.md). The [minimal custom manifests](../assets/README.md) intentionally provide ordinary channel transport; they are not complete Slack Agent-experience implementations.

Inspect the installed SDK before choosing handler helpers; no universal `app.agent()` registration API is assumed. [Slack Code](https://docs.slack.dev/ai/slack-code/) channels are an optional additional feature, not a prerequisite for ordinary channel intake.
