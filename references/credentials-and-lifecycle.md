# Tokens, new channels and undo

## Where tokens live

- **One private file per app:** for example `~/.config/slack-agent-team/slack-<seat>.env`, mode 600, in a mode-700 folder outside any repository.
- **Never paste a token** into chat, a prompt, a log, or a file in a repository.
- **The bot token (`xoxb-`)** reads and posts.
- **The app-level token (`xapp-`)** with `connections:write` is only for Socket Mode. Slack has no special "agent token". The AGENT badge is a display setting ([slack-apps-and-agents.md](slack-apps-and-agents.md)).
- **Check every token with `auth.test`** before using it: right workspace, right bot user.

## Adding a channel or a project

- **Reuse each assistant's existing app.** A new channel needs no new token: invite the bot and give it a session and listener for that channel.
- **A different workspace** needs its own app installation.
- **Create a separate app only for a concrete reason,** such as different scopes or a project that must be sealed off. See the [recommended layout](slack-apps-and-agents.md#recommended-layout-one-app-per-assistant-the-channel-is-the-project).
- **A persistent personal assistant** keeps its own account and memory. Adding it to a project channel, or removing it, never deletes the assistant.

## Undo

During setup, save a copy-paste undo script with the private setup record. When the user says "disconnect everything":
1. Stop the listeners, heartbeats and relays you started.
2. Remove the channel routes and any sessions you created for this channel.
3. Retire only the Slack apps you created. `auth.revoke` with an app's own bot token deactivates that bot and removes it from every channel ([auth.revoke](https://docs.slack.dev/reference/methods/auth.revoke/)).
4. Leave alone the apps, accounts and routes that existed before.

## Token rotation

Slack token rotation uses expiring access tokens plus a refresh token. Set up the refresh exchange before turning rotation on. Don't revoke the original token during the migration, because that can revoke the installation itself ([token rotation](https://docs.slack.dev/authentication/using-token-rotation/)).

Sources: [token types](https://docs.slack.dev/authentication/tokens/), [Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/).
