# Assets

| File | What it is |
| --- | --- |
| [team.example.json](team.example.json) | An example roster for the private setup record: who's on the team, their apps, token files, listeners and roles. Fake IDs. |
| [TEAM_CONTEXT.template.md](TEAM_CONTEXT.template.md) | The one short file every agent in a project channel reads. |
| [SHARED_MEMORY.template.md](SHARED_MEMORY.template.md) | Private shared memory for a personal-assistant team. |
| [slack-polling.manifest.json](slack-polling.manifest.json) | A minimal custom Slack app that reads channel history by polling. |
| [slack-socket.manifest.json](slack-socket.manifest.json) | A minimal custom Slack app that receives events over Socket Mode. |
| [pstack-source.json](pstack-source.json) | The reviewed pstack revision. |

Keep filled copies outside this public package.

## Manifests

These are starting points for **custom** apps. They aren't for vendor apps like ChatGPT, Claude, Cursor or Grok Bot, which use their own install flows ([Grok Bot](../references/grok-cursor-identity.md)). Rename each app for its product, as in "Codex" or "Claude Code", never for a project ([naming](../references/slack-apps-and-agents.md)).

Scopes:
- **Reading:** `channels:history` for public channels, `groups:history` for private ones. With Socket Mode, add the matching events, `message.channels` or `message.groups`. A bot still has to be a member of a private channel.
- **The lead's app:** add `groups:write.invites` (private) or `channels:write.invites` (public), so it can invite the participants the user chose.
- **Optional:** `reactions:write` for 👀, `users:read` for the roster, and `channels:read`/`groups:read` for channel details.
- **Socket Mode:** an app-level token with `connections:write`, created on the app's Basic Information page.

Adding scopes requires a reinstall. Check the granted scopes with the `x-oauth-scopes` header from `auth.test`.

These manifests give ordinary channel bots. Slack's AGENT badge is a separate, app-wide setting ([slack-apps-and-agents.md](../references/slack-apps-and-agents.md)).
