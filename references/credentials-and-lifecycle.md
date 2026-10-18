# Agent guide: temporary projects and persistent assistants

The setup agent performs these steps through available authenticated tools, desktop/browser controls, and secret storage. Ask the owner only for a concrete login/MFA/admin gate or missing material authorization; do not delegate routine setup back to them.

## Choose credential ownership before creating tokens

First distinguish the Slack app, bot user, workspace installation, token and Agent experience using [slack-apps-and-agents.md](slack-apps-and-agents.md). An AGENT label does not require a special agent-token type. For Grok Bot/Cursor, inspect the [native per-bot connection](grok-cursor-identity.md) before creating a custom app or asking for credentials.

| Situation | Recommended ownership | End of use |
| --- | --- | --- |
| Separate one-off project, same workspace | Reuse each assistant's plainly named workspace app; add a per-channel runner session, context and resource grants. Create a dedicated app only for a concrete boundary in [the recommended layout](slack-apps-and-agents.md#recommended-layout-one-app-per-assistant-the-channel-is-the-project) | Stop that channel's intake, reconcile work, retire project resources; keep the shared apps |
| One-off project that must be sealed off (different scopes, blast radius, owner, or workspace) | Dedicated custom Slack app/install, external secret namespace, runner session, resource credentials where appropriate, and project budget | Stop intake, reconcile work, retire project resources and revoke only dedicated credentials |
| Existing persistent personal assistant joining another ongoing channel | Reuse its supported account/identity and installed credential reference; add scoped channel/session/context routing | Remove that channel/task route without destroying the assistant |
| Persistent personal assistant temporarily helps a project | Keep personal identity/account; use a project-scoped session/context and scoped resource grants; create a dedicated project bot only if identity/access separation requires it | Retire project scope while preserving personal memory, account and other routes |
| Managed dot/vendor bot/session | Use vendor-owned install/login/account flow; record references it exposes | Disconnect only the intended contact method/environment/task under supported controls |

Example secret references: `secret-store/projects/PROJECT/assistant/slack-bot` for a dedicated project and `secret-store/personal/ASSISTANT/slack-bot` for a persistent assistant. These are reference names, never secret values.

A Slack OAuth token belongs to its app installation/account and workspace; it is not a newly scoped per-channel token. Creating another token for the same installation does not by itself isolate projects or create another teammate. Dedicated app membership plus explicit runtime routing/resource permissions creates the intended boundary. A separate visible custom teammate needs its own app/bot identity; changing message display names does not provide that identity.

“Persistent” describes the assistant's identity and state, not a promise that a literal token never expires. Rotate/refresh through the provider's actual lifecycle. Subscriptions, inference APIs, Slack credentials, and repository/calendar/mail permissions are separate.

## Add credentials for a one-off custom project

1. Inventory existing apps and secret references. Choose the project's workspace, private/public audience, participants, required resources, owner, budget, and retirement condition. Reuse an already correct dedicated setup.
2. Reuse each assistant's existing workspace app unless a boundary in [the recommended layout](slack-apps-and-agents.md#recommended-layout-one-app-per-assistant-the-channel-is-the-project) applies. Only then create a dedicated app through Slack's supported app-management UI/manifest flow. Name it for the assistant plus that boundary, never for a project it might later leave; select only required scopes from [the manifest guide](../assets/README.md). Install/authorize in the intended workspace through the available desktop or API route.
3. Store the installed **bot token** directly in the selected secret store under a project-specific reference. Never print/paste credentials into chat, skill files, prompts, or version control. Use a supported credential manager; local-file fallback requires restrictive platform-appropriate access outside the repo.
4. Add a separate **app-level token** with `connections:write` only for Socket Mode. For HTTP use its **signing secret**; for polling neither is required. Keep app-configuration/provisioning credentials out of workers.
5. Add a dedicated model/provider inference key with the authorized budget only if that custom runner requires it. A managed or subscription session may use its existing authenticated account and need no new API key. Separate project keys help attribution/revocation but do not add account capacity.
6. Bind secret references to the intended app/workspace/participant, project session, channel allowlist, and resource grants in the runner's supported configuration. Check `auth.test`, identity, actual scopes and membership; then follow [notifications.md](notifications.md) and prove a real round trip.
7. Save owner, purpose, installation IDs, secret-reference names, authorized uses, refresh/revocation mechanism, and retirement condition in the private [credential inventory](../assets/credentials.example.json). Use the same credential-reference object under each participant’s `credentials[]`; match its ID to the private inventory. All secret **values** remain in the secret store.

## Add or maintain persistent personal-assistant access

1. Locate the existing assistant account/session and its supported native integration before provisioning a custom bot. Preserve the assistant's identity and memory.
2. Reuse existing credential references when they cover the authorized workspace and actions. A new Slack workspace requires its own app installation and corresponding token/secret reference, even for the same persistent assistant. For a genuinely new workspace/install/provider, add a separately owned secret reference through its official flow; never borrow an unrelated project's credentials.
3. Scope each channel/person/purpose independently. Keep personal [shared memory](shared-context.md) separate from project context; a channel addition does not authorize broadcasting personal history.
4. Configure durable session mapping, notification preference, operator, budget and refresh/recovery owner. Revalidate grants after changes; test another existing route still works when adding a new one.
5. On removal of a temporary assignment, delete only that assignment's routes, queues, schedules, resource grants and context sharing. Preserve shared app installations, personal memory and credentials still serving other routes.

## Refresh, rotation, and retirement

Slack OAuth rotation uses expiring access tokens and refresh credentials; implement the supported exchange/refresh and secure persistence before enabling it. Serialize refresh operations for an installation. Do not apply a generic “revoke the old token” recipe to rotation migration: revoking the original credential can revoke installation authorization. [Slack rotation](https://docs.slack.dev/authentication/using-token-rotation/).

At project retirement: stop new intake, settle/cancel in-flight work, record uncertain effects, disable project schedules/listeners, revoke project-only credentials/grants, and archive/delete state according to retention policy. Check ownership before each revocation. On compromise, revoke the affected credential through the provider-supported process and revalidate its dependent routes. A successful secret-store write alone is not runtime acceptance.

Sources: [Slack token types](https://docs.slack.dev/authentication/tokens/), [Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/), [manifest configuration](https://docs.slack.dev/app-manifests/configuring-apps-with-app-manifests/).
