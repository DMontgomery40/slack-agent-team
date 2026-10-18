# Grok Bot, Cursor, and the actual participant

Read when Grok Bot, a Grok model, Cursor, or a delegated cloud worker appears in a team. These can share account infrastructure while representing different assistants, sessions, and authority. Inspect the installed route before provisioning tokens or counting teammates.

## Identify the relationship

| Observed participant | What to establish |
| --- | --- |
| Grok Bot personal assistant | Its actual personal bot, persistent context, account, connected tools, and native contact methods |
| Grok Bot Team Bot | The published bot, owner/team, native Slack installation, linked calling accounts, and per-conversation behavior |
| Grok model selected in Cursor CLI/editor | Cursor runtime, actual selected model, local session, enabled tools, and any custom Slack relay |
| Cursor Cloud Agent delegated by a bot | Parent bot, separate worker/task, repository/environment, model where exposed, result destination, and inherited scope |
| Native `@Cursor` Slack app | New Cloud Agent from a new mention/conversation versus follow-up in its existing thread; actual `model=`, `repo=`, `env=` and worker/pool selection, execution location and result thread. This is not automatically an editor/CLI chat or a Grok Bot worker. |
| Independent Cursor session | Its own account/session, responsibility, Slack identity and subscriptions; shared branding is insufficient to merge it with another participant |

Official Grok Bot setup uses Cursor account linking and creates a separate Slack app for each Team Bot. This is a documented product relationship, not merely a naming inconsistency. Grok Bot's model selection is managed internally; record runtime as Grok Bot and model as vendor-managed/unreported unless current product evidence exposes more. Its product name does not establish an exact backend model. A Grok model explicitly selected in Cursor CLI is a different execution route. [Team Bots](https://docs.x.ai/grok-bot/team-bots), [Grok Bot models](https://prod.cursor.com/help/grok-bot/models).

For the native Cursor launcher, verify current routing options and resulting task metadata. Its supported worker may be hosted or a registered machine; “Cloud Agent” alone does not prove execution location. [Cursor Slack integration](https://cursor.com/docs/integrations/slack).

Shared infrastructure and delegation do not establish shared session, memory, permissions, or decision seats. See the dated [research record](research.md) for local corroboration. Keep private identifiers and source excerpts in the private setup record.

## Agent-executed discovery

1. Identify the requested existing assistant in its actual UI or supported session controls. Inspect relevant local app metadata and scoped project configuration when names conflict. Read public docs alongside the installed version; neither a bot's self-description nor a cached task listing proves current operation.
2. Map logical participant, product, account, runtime, model visibility, session/task, parent/worker relationship, Slack app ID, bot-user ID, installation, and receiving mechanism. Distinguish the inbound integration from the posting identity: a Cursor-account listener can wake a bot which replies using a different custom app's token. Verify both installations' channel visibility. Mark each proposed relationship **same**, **different**, or **unknown**, with dated evidence. Use the optional `identity_relationships` in the [team template](../assets/team.example.json).
3. Preserve the user's decision/ownership structure. A delegated worker normally returns to its parent's assigned task and has the parent's bounded scope; it does not acquire an independent vote or wider authority merely by appearing as another app. Record explicit independent roles when the user established them.
4. Verify context transfer separately. A shared account or plan does not transfer private assistant memory to a worker. A routine may launch a fresh automation child of a persistent bot; a Slack mention may launch a fresh cloud run. Record `invocation_kind` and the context source instead of calling either a continuation of the main desktop conversation. Supply the authorized task/context pointer and require the intended session's receipt. Keep unrelated personal context outside the worker's project.

**Done:** the roster can answer which process/session does the work, which Slack identity speaks, which participant owns it, and which relationships remain unknown.

## Prefer the actual native connection

For an existing Grok Bot, inspect its own supported Add to Slack/contact-method flow first. For a Team Bot, the agent opens its details, uses **Bring to your team's Slack**, connects the intended workspace through the Cursor authorization page, verifies the resulting bot-specific Slack app, and adds that bot to the agreed channels. Complete existing authorized account-linking flows through the available UI; surface only an actual login/MFA/admin gate. Do not replace an existing personal bot with a newly published Team Bot merely to simplify setup. [Native Team Bot setup](https://docs.x.ai/grok-bot/team-bots).

Use custom Slack app credentials only when the selected local/API runner actually consumes them. A managed bot's native install does not require the operator to extract its private token and paste it into chat. The separate xAI API-key Slack app, a Team Bot, and a custom Cursor CLI bridge are distinct routes. [API-key app](https://slack.hooks.x.ai/).

Read [listeners.md](listeners.md) for Team Bot mentions and thread following versus a channel-listener routine. Record the real receiving route before inviting a second visible identity. If the intended existing session is busy, queue a bounded consultation through its owner; a fresh review session must be labeled as such.
