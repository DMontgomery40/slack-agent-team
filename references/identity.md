# Slack identities and runtime access

The inspected team has distinct bot credentials for Claude Code, Codex and Muse Code. They identify the author of posts. Claude's watcher reads with its bot token; workers' task invocations use their existing CLI authentication.

| Item | What it provides |
| --- | --- |
| Slack app / workspace installation | App configuration and the grants approved for that installation |
| Bot token | Permission to make Slack Web API calls as that installed bot |
| Bot user ID | The user identity used in mentions and posted-message authorship |
| Channel membership | Access to the channel, subject to the token's scopes |
| Watcher / vendor receiver | Delivery of messages to a runtime, when configured |
| Model session / harness | Reasoning, tools, repository access and task execution |

An APP/AGENT label does not create a worker session or a special token that makes it listen. A model name also does not identify a Slack bot. Two participants can share a vendor or harness and still have different roles and identities.

## Inspect and reuse

Use `auth.test` for each credential and check membership and grants for the target channel. Preserve existing app names and installations unless the user requests a change. Multiple similar-looking apps can serve other channels or owners; they are not evidence that consolidation or revocation is needed.

For a new ordinary channel bot, the setup agent creates/installs the app through the workspace's supported process, obtains its bot token and invites its bot to the intended channel. Request scopes for the operations actually used. The helper uses:

- `auth.test` to resolve its identity;
- `conversations.history` for top-level history (`channels:history` for public channels or `groups:history` for private channels, with membership);
- `conversations.replies` for the limited thread reads described in the delivery guide;
- `users.info` for display names (`users:read`; a failed lookup falls back to the user ID);
- `chat.postMessage` to post (`chat:write`).

Verify thread access with the actual token; a successful top-level read does not prove every surface is readable. The observed credentials have additional grants, but this package does not require their complete scope list. Preserve channel privacy and follow the workspace's installation/approval process.

Store credentials through the environment's existing secret facility. The helper reads a selected environment variable and does not print token values. A bot token's access is broader than the `SLACK_CHANNEL_ID` supplied to this helper; that variable selects the destination and does not narrow the Slack grant.

The history-polling route does not use an app-level Socket Mode token. Socket Mode, vendor apps, assistants and coding CLIs have distinct receiving/authentication paths. Inspect those independently when adding them.

Sources checked 28 October 2026: [token types](https://docs.slack.dev/authentication/tokens/), [history](https://docs.slack.dev/reference/methods/conversations.history/), [replies](https://docs.slack.dev/reference/methods/conversations.replies/), [posting](https://docs.slack.dev/reference/methods/chat.postMessage/).
