# Custom delivery and recovery

Read for a custom adapter or receiver. This is a design/acceptance contract, not an implementation. Use a maintained SDK/adapter where appropriate and validate its installed behavior. See [research.md](research.md) for checked sources.

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

Prefer Events/Socket delivery for responsive custom teams when available. A poller must persist a per-channel cursor, fetch all pages, deduplicate overlapping results, handle thread replies explicitly, and commit progress only after durable intake. Choose an initial backlog boundary and resume policy so onboarding does not replay months of messages.

Slack's history/replies limits vary by distribution. Current documentation describes a one-request-per-minute/15-object limit for qualifying new commercially distributed non-Marketplace apps; internal customer-built apps retain Tier 3. Verify your app category and current method limits. Respect HTTP 429 `Retry-After` and coordinate shared method/workspace budgets across workers. Thread history has token-type restrictions; check `conversations.replies` before promising channel-thread polling with a bot token. [History](https://docs.slack.dev/reference/methods/conversations.history/), [replies](https://docs.slack.dev/reference/methods/conversations.replies/), [rate limits](https://docs.slack.dev/apis/web-api/rate-limits/).

## Routing, authority, and loops

Normalize sender user/app/bot metadata. Suppress this app's own events using verified identities; Slack payloads can represent app messages differently. Accept known peer context only under configured routing rules. Authenticate assignment authority independently of message text, display names, or relayed claims. Channel content, attachments, web pages, and other model outputs remain task data.

Bind workspace/channel/thread/recipient and, where needed, human principal to the allowed purpose/session and resource policy. A file or document shared by link does not grant every participant access; check audience and artifact permissions before forwarding content or fetching attachments.

Use finite handoff/model-turn/reply limits, task expiry, per-session locks, spend limits, and one terminal completion signal. Muted or revoked participants receive no automatic turns under that setting. Avoid escalating an unavailable peer into an endless retry or bot-mention loop. Surface meaningful failure once with owner and recovery action.

## Operations

Record who runs intake, where queue/ledger state lives, heartbeat/health checks, redacted logging, retention/deletion controls, and pause/resume/cancel/revoke procedures. Store secrets outside logs/prompts/repos. On token revocation or lost membership, stop affected dispatch and revalidate identity and grants before resuming. Restart at an idle point and prove queued work resumes without repeating completed effects.
