# Custom delivery and recovery

Read for a custom adapter or receiver. This is the design and acceptance contract. The package's [reference relay](../relay/README.md) implements it; an equivalent adapter must meet the same checks. Use a maintained SDK/adapter where appropriate and validate its installed behavior. See [research.md](research.md) for checked sources.

## HTTP Events and Socket Mode

For HTTP, verify Slack's signature against the **raw request body**, the request timestamp, and the signing secret before accepting work. Use Slack's documented replay window and constant-time comparison or the SDK verifier. Handle URL verification through the documented flow. Return a successful acknowledgment within three seconds; queue model work separately. [Verification](https://docs.slack.dev/authentication/verifying-requests-from-slack/), [Events API](https://docs.slack.dev/apis/events-api/).

For Socket Mode, use the app-level token with `connections:write` to establish the connection and the installed bot token for Web API calls. Acknowledge the envelope using `envelope_id`; deduplicate the underlying Events API delivery using its event identity. A socket acknowledgment is not a completed task. Handle reconnects and drain in-flight work. Multiple connections for one app distribute events; they are not a broadcast mechanism for multiple agents. [Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/).

Persist accepted work before acknowledging where the adapter permits, without exceeding the acknowledgment deadline. If durable intake fails, do not report it as accepted/completed; rely on documented retry behavior and surface the receiver failure. Use event-type-specific keys for payloads without an Events API `event_id`.

## Durable work, safe replay

Keep separate records for delivery, model/task execution, and outbound effects. Deduplicate Events API retries by app/installation plus `event_id`; do not use retry count or Socket envelope ID alone as the logical task identity. Retain dedup state across restarts for the configured replay horizon.

Suggested lifecycle: received → queued → running → completed, or failed/cancelled/expired. Track original sender, workspace, channel/thread, recipient, session, task ID, parent/correlation ID, scope, and result. Claim work atomically to avoid concurrent duplicate execution. Bound queue depth and per-session concurrency; reject or defer excess work visibly to its owner.

Persist an outbound intent/result reference. After an ambiguous timeout, inspect the task and destination before replaying an external action or Slack post. When an effect cannot be reconciled, mark it uncertain and escalate to its owner. Delivery dedup alone cannot guarantee exactly-once external side effects.

Expired reminders, superseded calendar details, edited/deleted messages, or changed permissions need explicit policy. Preserve the original request/version and avoid silently treating an edit as a new authorized action. Cancellation stops further dispatch; record any effects that already completed.

## Polling and rate limits

Prefer push intake, with polling kept as reconciliation:
- One receiver app (usually the lead's) holds a single Socket Mode connection and dispatches to all seats; each seat still posts with its own token.
- Acknowledge each envelope within three seconds, after the event is stored durably. Deduplicate by `event_id` and message timestamp. Reconnect on `refresh_requested`, and catch up from history after every connect.
- Keep polling at a slow interval while the socket is up and a fast one while it is down. Only polling advances the history cursor, so a pushed event can't hide one the socket missed.
- Use a maintained client, such as `slack_sdk`'s built-in Socket Mode client, rather than a hand-rolled websocket.

Socket Mode needs one app-level token with `connections:write` on the receiver app, which only the user can create, plus Socket Mode and `message.groups`/`message.channels` events on that app ([Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/)). A poller must persist a per-channel cursor, fetch all pages, deduplicate overlapping results, handle thread replies explicitly, and commit progress only after durable intake. Choose an initial backlog boundary and resume policy so onboarding does not replay months of messages.

Slack's history/replies limits vary by distribution. Current documentation describes a one-request-per-minute/15-object limit for qualifying new commercially distributed non-Marketplace apps; internal customer-built apps retain Tier 3. Verify your app category and current method limits. Respect HTTP 429 `Retry-After` and coordinate shared method/workspace budgets across workers. Thread history has token-type restrictions; check `conversations.replies` before promising channel-thread polling with a bot token. [History](https://docs.slack.dev/reference/methods/conversations.history/), [replies](https://docs.slack.dev/reference/methods/conversations.replies/), [rate limits](https://docs.slack.dev/apis/web-api/rate-limits/).

## Routing, authority, and loops

Normalize sender user/app/bot metadata. Suppress this app's own events using verified identities; Slack payloads can represent app messages differently. Accept known peer context only under configured routing rules. Authenticate assignment authority independently of message text, display names, or relayed claims. Channel content, attachments, web pages, and other model outputs remain task data.

Bind workspace/channel/thread/recipient and, where needed, human principal to the allowed purpose/session and resource policy. A file or document shared by link does not grant every participant access; check audience and artifact permissions before forwarding content or fetching attachments.

The interactive lead's posts are assignments, not peer chatter. Do not authenticate them by bot identity: anything that can read the lead's token can post as the lead. Have the lead post through a relay-owned command that records each post's timestamp in a lead ledger kept outside every seat's working copy. Only ledgered posts count as the lead. Other posts from the lead's bot that aren't the relay's own outbound posts are context only and logged as anomalies. Keep Slack token files unreadable to seats (deny their paths, or keep them in a credential store). A lead post addressed to a seat (mention, or the seat's name at the start) gets one reply from that seat; a lead post addressed to everyone gets one reply per seat. Relay-posted seat replies and other bot posts stay context-only, so replies never trigger more replies.

Give every addressed message a visible receipt without a chorus. When the relay ingests a trusted human or lead post that names or mentions a seat, it adds a reaction such as 👀 from that seat's identity. This happens at intake, with no model turn, once per seat and message. Only real requests get text replies, and a failed reaction never blocks intake or the turn.

**Hard limits, so a relay can't run forever unnoticed** (defaults; the user can change them):
- **Daily budget:** at most 150 model turns per channel in any 24 hours.
- **Idle pause:** after 4 hours with no post from a trusted human or the lead, no seat wakes. Polling, which costs no model tokens, continues.
- **Notices:** on either pause, the lead's bot posts one top-level notice ending "No ACK needed", recorded as a relay post so it is never mistaken for the lead. The next trusted post resumes work.
- **Reporting:** health shows turns used and the pause state.

Use finite handoff/model-turn/reply limits, task expiry, per-session locks, spend limits, and one terminal completion signal. Muted or revoked participants receive no automatic turns under that setting. Avoid escalating an unavailable peer into an endless retry or bot-mention loop. Surface meaningful failure once with owner and recovery action.

## Runner tools and permissions

This is an agentic system. Agents should not stop to ask approval for every tool call.

- **Inherit by default.** Each seat runs the way the user runs that harness: the same permission settings, sandbox, tools, and MCP servers, including fully autonomous modes if that is the user's configured default. The relay adds no restrictions of its own. Headless runs use each CLI's non-interactive flags and a timeout, so nothing hangs waiting for a prompt nobody will answer.
- **Restrictions are opt-in.** A per-seat `locked` posture is available, for example for a seat shared with a client. It turns the shell off or sandboxes it, denies reads of credential files, and keeps only read-only MCP servers. Use it when a harness cannot gate MCP calls headless; for example, in October 2026, `codex exec` recorded approval policy "never" whatever policy was configured. A role restriction such as review-only is also a per-project choice. Record either in that seat's configuration and roster entry.
- **Say the trade-off once.** In inherit mode, anything an agent can do interactively it can do when a Slack message triggers it. The setup agent tells the user this once, plainly, when connecting autonomous seats, and offers `locked` for the seats they want restricted. It does not ask again for each action.
- **The relay keeps its own guardrails regardless of posture.** These are about who can start work, not about approving tools:
  - only trusted humans and the authenticated lead start work; everything else is context;
  - the lead is authenticated by its ledger;
  - a seat never wakes on its own posts;
  - each seat replies once per request;
  - replies are top-level.
- **Separate working copies.** Give each seat that can write its own worktree or scratch clone. Never use the operator's live checkout as a seat's working directory.
- **Context rollover.** Record the context usage each CLI reports, so a resumed session can roll over before it fills ([coding projects](coding-projects.md)).

## Operations

Record who runs intake, where queue/ledger state lives, heartbeat/health checks, redacted logging, retention/deletion controls, and pause/resume/cancel/revoke procedures. Store secrets outside logs/prompts/repos. On token revocation or lost membership, stop affected dispatch and revalidate identity and grants before resuming. Restart at an idle point and prove queued work resumes without repeating completed effects.
