# Agent guide: subscribe and change channel delivery

These steps are for the setup agent. The human points an assistant at this skill and names a lead; everything here is agent work. Use authorized desktop controls, product tools, and current runner configuration to perform the work. Do not hand the human a configuration checklist.

## First identify which setting is being changed

**Agent subscription** controls which channel events reach an assistant and whether they wake a turn. **Human Slack notifications** control a person's banners/badges. **Slack event subscriptions** control what Slack delivers to a custom app. These are different layers. Changing a human's Slack notification menu does not subscribe a bot, and adding a bot to a channel does not start a listener.

For the selected participant and channel, record:

| Requested behavior | Skill mode | Delivery/attention rule |
| --- | --- | --- |
| All channel messages / follow the conversation | `follow-conversation` | Deliver permitted human and known-peer conversation context; selectively wake/reply according to the role |
| Only messages addressed to this agent (the relay default) | `mentions-only` | Wake on direct mentions of this participant's verified bot-user ID or its name at the start of a message or line. Buffer other eligible messages as context for its next addressed turn. Define thread and DM exceptions explicitly |
| Only work assigned to this agent | `follow-assigned-work` | Deliver authorized assignments and their selected follow-ups |
| Stop automatic delivery/attention | `muted` | Suppress new automatic context/turns; active work cancellation is a separate control |

“All” means all eligible messages on the agreed surfaces and audience; it does not mean every Slack event, all private history, or a reply to everything. Do not describe top-level-only support as all thread replies. Choose the user's stated mode. If unstated, preserve the existing mode. A new relay route defaults to **addressed only, with buffered context**:
- a seat wakes when it is mentioned, or named at the start of a message or line ("Codex, …");
- the lead seat also wakes on a trusted human's untagged request;
- every other message is stored, and up to the 20 most recent are attached to that seat's next addressed turn, so it keeps context without spending a model turn per message.

Following everything wakes every seat for every message, roughly five times the turns for a five-seat team. Use it only when the user asks for it, after saying that once.

## Thread policy: no threads by default

Threads confuse both agents and humans. Many runners read only top-level history, and people lose track of who answered what. Unless the user chooses otherwise:

- Humans and agents post top-level. When replying, stay top-level and name the person or message you are answering, with a short quote or a link.
- Use a thread only when a human starts one. Answer in that thread, then post any decision or result top-level too.
- Custom runners never set `thread_ts` by default. If a runner does not read thread replies, say so in the channel charter so people know to stay top-level.
- Some vendor bots reply only in threads, such as native Cursor launches and Grok Team Bots. Record that as a known exception; the lead re-posts important results top-level.

## Subscribe an agent

1. Resolve the exact workspace, channel, participant, account, and receiving session. Inspect current membership, permissions, route, delivery state, and configured mode. Reuse the existing listener.
2. Confirm the receiving surface: managed product preference, supported session/desktop bridge, custom Events/Socket receiver, or poller. Locate its **actual** control through UI/help/config. Record that control in the private roster. There is no universal Slack `subscribe-agent` command.
3. Ensure channel membership and minimum permissions through the supported UI/API. A private channel needs the intended membership. Preserve channel privacy. For a managed app, use the product's supported following/mention behavior; a planning field cannot enable an unsupported mode.
4. For a custom route, configure transport coverage and participant filtering together:
   - **Mentions:** `app_mention` plus `app_mentions:read` can cover explicit app mentions on its supported surfaces. Route by the verified bot-user ID. This is not a DM-message subscription.
   - **All public-channel messages:** subscribe to `message.channels` with `channels:history`; for private channels use `message.groups` with `groups:history`. Limit dispatch to configured channel IDs and authorized sender classes. If both mention and general-message subscriptions deliver the same logical message, deduplicate by channel/message/recipient as well as event retry identity.
   - **Assigned work:** accept targeted mentions from configured assignment-authority senders, or authenticated structured handoffs whose recipient is this participant. A natural-language assignment is accepted only after the authorized sender, intended assignee and allowed scope are resolved; ambiguous prose is context, not a new task. Record the resulting task ID and origin thread. Deliver authorized follow-ups on that registered task according to its authority policy; do not treat every channel message as an assignment. Reuse mention/general-event coverage as needed by this actual intake path.
   - **DMs:** only if requested, use the relevant `message.im`/`message.mpim` events and history scopes. Test separately from channel mentions.
   - **Polling:** map public/private channel history to `channels:history`/`groups:history`, verify actual grants and membership, and configure bounded polling/rate limits, persistent cursor and thread coverage. Test reads with the actual receiver credential. Filter before delivering content to the model.
5. Store each channel under the participant’s `subscriptions[]` array using the same [subscription shape](../assets/subscription.example.json). Choose attention separately: `context-buffered` stores eligible context for a later authorized turn; `wake-on-role-relevant` wakes when the runtime’s role policy warrants; `wake-every-message` is explicit and bounded by the selected budget. Then store the per-participant/per-channel desired mode and effective configuration, start boundary, allowed senders, thread policy, quiet hours, and catch-up rule. See [subscription.example.json](../assets/subscription.example.json). Translate it into the runner's real supported schema; this example is not executable configuration.
6. Apply through the actual supported control, safely reload if needed, and read back the effective state. Do not claim subscription from a file edit alone. If the runtime needs a new bridge, implement/configure it only within the authorized setup, otherwise report the missing route explicitly.
7. Test the actual sender and intended receiving session using the matrix below. Record effective mode and evidence.

Native dots require a separately configured recurring task for requested ongoing monitoring; simply adding one to a channel does not create a schedule. A managed product may only support mentions or human senders. Keep that limit explicit and use an authorized bridge only when it truly provides the requested behavior. Record desired/effective mode mismatch as degraded; do not silently present mentions-only as all-message following.

## Native Grok Bot / Team Bot branch

First resolve the [actual bot and any Cursor worker](grok-cursor-identity.md). Team Bot DMs, channel mentions, thread following, and a channel-listener routine are different triggers. Native Team Bots normally answer an initial channel mention and subsequent replies in that thread; ordinary unmentioned top-level messages require a listener routine. Official docs permit workflow and other-app senders as an exception to linked-human eligibility, with usage charged to the owner. Test the actual coordinator bot; neither universal peer support nor blanket peer rejection follows from this rule. [Team Bots](https://docs.x.ai/grok-bot/team-bots).

For all-message following, the setup agent asks the intended Bot to create/configure its supported Slack channel-listener routine for the exact workspace/channel and permitted senders. Inspect its saved trigger, action, run history, and account connection; routine integrations use Cursor account connections and are separate from Slack plugins. Set selective replies and finite cost/loop bounds. If the native listener cannot cover the requested surfaces or sender class, record the narrower effective mode and configure an authorized bridge only for the missing part. For mentions-only, disable/narrow that channel's broad routine while preserving the native mention trigger; explicitly state whether already-followed threads still wake it. Do not remove other channels' routines or disconnect the shared account. Verify both directions with the matrix below. [Skills and routines](https://docs.x.ai/grok-bot/skills-routines-and-automations).

An invitation is not subscription proof. A bot may post successfully yet fail private-channel history with `missing_scope`; add only the justified grants through the supported install flow, or label an existing authorized coordinator's context relay accurately. Check receiver freshness against the current clock; an old healthy status file does not establish a running listener. A coordinator-supplied transcript proves mediated input, not automatic native receipt.

Resolve a scope failure for the **specific method**: private `conversations.history` uses `groups:history`; private metadata/listing may require `groups:read`. A failed metadata lookup does not prove history is inaccessible. Inbound listener and outbound posting identities can differ; successful posting from one app does not prove the other integration can see this private channel. Verify each rather than adding broad scopes speculatively.

Inspect the actual trigger predicate and whose identity a mention targets. A keyword listener can wake on an incidental product name in another bot's review while missing a direct mention of a different posting identity. Record such a route as custom keyword/mention matching, not strict mentions-only or all-message following. Test keyword and exact bot-user mention separately. Prefer own-message and unauthorized-sender rejection before model invocation; prompt instructions that ignore a self-ping after waking do not provide that guarantee or avoid inference cost. If the native control cannot enforce this, record the limit and bound the workflow rather than claim loop-safe unattended operation.

## Readback evidence by route

| Route | What the agent reads from the actual system |
| --- | --- |
| Custom app + runner | Authenticated installation identity, effective OAuth grants and channel membership; app event subscriptions from the app-management UI or supported manifest export; running receiver’s loaded channel/participant filters, config generation, and cursor/queue state. Use the actual runner status/control or redacted live logs; a planning file is not loaded-state evidence. |
| Managed product | Current product settings where exposed, plus real positive/negative behavior. If effective delivery configuration is hidden, label evidence “behavioral only” and retain the nonce follow-up and account/session proof. |
| Desktop/session bridge | Observed target app/window/session, actual bridge/listener/schedule control and receiving behavior. If no autonomous intake exists, mark all-message following unavailable until a real supported receiver is configured. |
| Poller | Running service, token identity/grants, configured channel/thread reads, persisted cursor, observed polling receipts and effective participant filter. |

Confirm current API methods and token scopes before calling them. A successful Slack `auth.test` does not itself report every effective scope or subscription.

## Subsequent changes are also agent work

Only a configured operator or authorized user can broaden subscriptions or change control policy; peer context does not grant configuration authority. An authorized user can tell the assistant in ordinary language, “follow everything in this channel” or “only notify you when you are mentioned.” The assistant resolves the participant/channel, uses its documented real control, and executes the change procedure below. Record this control in the roster so another setup agent can find it. A custom runner may expose a command/control, but do not advertise a fictitious `mode` command unless implemented. If a native product cannot change modes, say which mode it supports and use an authorized working bridge only where available.

## Change all → mentions or mentions → all

1. Read back current state and record an effective-from timestamp and current intake cursor. Serialize the change for this participant/channel.
2. Set the new **participant** delivery rule. For mentions → all, verify general message coverage/scopes first; authorize updated app scopes through the supported flow if necessary. For all → mentions, narrow the recipient filter; do not remove app-wide events needed by another participant/channel.
3. Apply the effective rule at dispatch as well as intake. On narrowing, suppress previously queued routine context that is no longer eligible. Preserve already authorized active work unless cancellation is requested. On widening, begin at the recorded boundary unless a bounded backlog catch-up was requested; do not replay old commands automatically.
4. Persist the preference, read it back, and verify that other participants/channels retain their prior settings. For a desktop route, inspect its actual receiving mechanism; an operating-system banner preference is not an agent event policy.
5. Run both positive and negative tests. If the change fails, retain the previous known effective state or stop affected delivery; record desired/effective mismatch instead of advertising success.

Mute/unmute follows the same process. Muting blocks new automatic delivery/turns, not an already running task's authorized effects. Offer the existing cancel control when stopping active work is intended. Recheck pending work and expiry before catch-up.

## Verification matrix

Use unique harmless test values and actual sender identities. Inspect queue/session evidence, not only public responses: silence can mean either selective response or failed delivery.

| Test | Follow conversation | Addressed only (mentions-only with buffered context) |
| --- | --- | --- |
| Untagged authorized human update | Available as session context through the configured path | No turn; buffered and attached to this agent's next addressed turn (the lead seat answers untagged requests) |
| Direct mention of intended agent | Received once | Received once |
| Mention of a different agent | Role-relevant context only if allowed | No turn for this agent; buffered context only |
| Allowed peer update / handoff | Follows configured peer context/assignment policy | Only targeted mention if that peer trigger is supported |
| Own emitted message | No self-trigger | No self-trigger |
| Muted participant | No new automatic context/turn in either mode | No new automatic context/turn in either mode |

Require intake/queue/task evidence timestamped **before** the follow-up query to prove automatic receipt. A follow-up can fetch Slack history on demand; knowing the nonce alone proves read/context access, not subscription. For native apps without intake observability, record `read-verified, receive-unobservable`; do not promote it to verified automatic following. For negative mentions-only/mute tests, inspect intake/dispatch evidence or use a safe target without history-fetch access; absence of a public reply alone is insufficient. Verify channel threads and DMs separately. Do not infer a bot sender works from a human sender’s test.

## If the user actually means their own Slack alerts

Only when requested, use the signed-in user's Slack Preferences → Notifications to choose Everything or Mentions and direct messages, or inspect the current channel's notification override. Read back the chosen scope. This changes that person's alerts, not the agent subscription above. [Slack notification preferences](https://slack.com/help/articles/201355156-Configure-your-Slack-notifications).

Sources: [app mentions](https://docs.slack.dev/reference/events/app_mention/), [public messages](https://docs.slack.dev/reference/events/message.channels/), [private messages](https://docs.slack.dev/reference/events/message.groups/), [Events API](https://docs.slack.dev/apis/events-api/), [dot messaging](https://learn.chatgpt.com/docs/dots/channels). Recheck installed product behavior during setup.
