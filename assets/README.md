# Manifest templates

These are minimal starting points for **custom** apps, not vendor-managed apps and not installed configurations. JSON syntax is locally checked; Slack server-side validation and installation must occur during a real setup. Replace `Project Researcher` and `project-researcher` before creating each distinct role.

| File | Receive mechanism | Credentials |
| --- | --- | --- |
| [slack-polling.manifest.json](slack-polling.manifest.json) | Your runner polls public-channel history | Installed bot token |
| [slack-socket.manifest.json](slack-socket.manifest.json) | Socket Mode delivers explicit app mentions | Installed bot token plus separate app-level token with `connections:write` |

Use [notifications.md](../references/notifications.md) to apply and verify per-participant subscription changes, and [credentials-and-lifecycle.md](../references/credentials-and-lifecycle.md) for project versus persistent credential ownership.

The Socket template receives mentions only. Add history permissions if the runner fetches conversation context. Bot-originated mentions need their own real acceptance check; if your receiver requires general channel message events, add `message.channels` plus `channels:history` and enforce routing filters. For private-channel history use `groups:history`; for corresponding general events use `message.groups`. A private-channel bot still needs membership.

Other optional operations: `channels:read`/`groups:read` for relevant discovery and metadata, `users:read` for user-profile checks, `channels:join` for public self-join, `reactions:write` for reactions. Select additional scopes from the actual methods used. The templates rely on an authorized workspace user adding bots to known channels; they do not give workers channel creation/invitation authority.

Leave `chat:write.public`, file access, user tokens, and DMs out until the role needs them. A least-privilege manifest may not run an old helper that unconditionally calls `users.info`; either add its justified scope or adapt the identity check. Review actual granted scopes after installation.

## Agent-applied mentions → all public messages change

Merge this fragment into the existing Socket manifest; retain other needed events/scopes. This adds public-channel coverage. For private-channel coverage add `message.groups` and `groups:history` only when required. Apply the update through Slack’s supported UI/API, complete scope reauthorization/reinstallation where required, and verify actual grants and loaded runtime filters before claiming the mode changed. The JSON file itself has no effect on the running app.

```json
{
  "oauth_config": {"scopes": {"bot": ["app_mentions:read", "chat:write", "channels:history"]}},
  "settings": {"event_subscriptions": {"bot_events": ["app_mention", "message.channels"]}}
}
```

This is a merge fragment, not a full replacement manifest. See [notifications.md](../references/notifications.md) for per-participant filtering, duplicate logical messages, readback, and switching back without disrupting other routes.

## Project configuration

[project.example.json](project.example.json) is a **planning contract**, not an OpenClaw, Slack, or Codex runtime schema. Required unresolved values are explicit strings. Budget amounts are intentionally null until chosen; null does not mean unlimited. Translate this record into the selected runner's current supported schema and validate it there.

Start with [team.example.json](team.example.json) for any team or [personal.example.json](personal.example.json) for daily assistance. The project example adds optional coordinator, researcher, implementer, and reviewer roles. Choose each product/provider explicitly. Hermes and OpenClaw may already be in use; inventory them without automatically adding a connection. Native vendor identities may be shared across channels; custom identities are distinct by default. Secret references are locations/names only, never values. For a managed product, null out raw credential/session/model fields it does not expose and record its account/task/environment reference plus the limitation. In mentions use `bot_user_id` (`U…`), not `bot_id` (`B…`).
