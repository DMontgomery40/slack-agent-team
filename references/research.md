# Public Slack skill research

Reviewed official sources on October 17, 2026. Recommendations below are engineering judgments where marked; vendor capabilities still require installation-specific acceptance tests. Original skill was read, not changed.

## Highest-value changes

1. **Make work scope general.** Start from a purpose (daily assistant, shared operations, research, delivery coordination, or software project). Repository and checkout are optional resources. Core binding should be workspace/channel + agent identity → owner + actual runtime/session + authorized resources + receiving behavior. Add examples for an everyday assistant and a delivery team; do not require developer tooling for the former.
2. **Separate four proofs:** installed identity; inbound wake-up; access to required resources; completed work returned under the intended identity. A Slack connector in a local session proves tools, not wake-up. A dot contact method is a managed route, not a custom relay token. Cross-agent intake must be tested from the actual peer sender.
3. **Promote durable intake and side-effect reconciliation** into an explicit checklist: authenticated input → durable receipt/dedup → fast transport ACK → bounded work queue → task state → result outbox/readback. This sequence is a recommendation, not a guarantee provided by Slack. Do not describe transport delivery as exactly-once execution.
4. **Keep defaults configurable:** personal-private versus shared-team context; notification mode; thread versus top-level summaries; permitted senders and assignment authority. Do not publish the original user's name, project channel ownership, model names, local paths, or organizational preferences as universal defaults.

## Delivery and transport

**HTTP:** Slack expects 2xx within three seconds and documents retries immediately, after one minute, then after five minutes. `event_id` is globally unique. `x-slack-retry-num` and `x-slack-retry-reason` are diagnostics, not fresh work identifiers. Recommendation: key the event receipt ledger by app/workspace/event ID; key business actions separately by task/action ID, because separate subscriptions or multiple bot identities can observe the same underlying message. ACK duplicates successfully without re-running work. Persist receipt before accepting if the architecture can meet the deadline; fail/retry rather than silently lose unqueued work. [Events API](https://docs.slack.dev/apis/events-api/).

**HTTP verification:** verify the signature against the raw body before parsing; use the signing secret, request timestamp, HMAC-SHA256 and constant-time comparison. Slack's example rejects timestamps more than five minutes from local time. Use current Bolt signature support where appropriate, and retain it through proxies/middleware. Test stale/tampered requests. [Verifying requests](https://docs.slack.dev/authentication/verifying-requests-from-slack/).

**Socket Mode:** ACK the received `envelope_id`; this is transport receipt, distinct from the inner Events API `event_id` used for processing deduplication. The socket is pre-authenticated, so HTTP signing-secret validation is not its inbound verification mechanism. Reconnects are expected. Up to ten connections are supported, with unspecified payload distribution; they do not broadcast a copy to each role. A receiver fleet needs shared processing state. [Socket Mode](https://docs.slack.dev/apis/events-api/using-socket-mode/).

**Transport choice:** Slack recommends HTTP for deployed production applications and requires HTTP for Marketplace submission. Socket Mode is supported for distributed applications and useful behind firewalls. A public documentation/skill repository is not itself a Marketplace app: do not confuse publishing this skill with choosing a commercial distribution model. [HTTP versus Socket Mode](https://docs.slack.dev/apis/events-api/comparing-http-socket-mode/).

## Polling, rate limits, and posting

New commercially distributed non-Marketplace apps/installations have `conversations.history` limits of one request per minute and fifteen returned objects. Marketplace and internal customer-built apps retain Tier 3. Current documentation explicitly exempts existing installations from the new posted limits; do not repeat older universal March 2026 migration statements. Identify app distribution class before selecting polling intervals. [History](https://docs.slack.dev/reference/methods/conversations.history/).

`conversations.replies` documents the same distribution-specific limits. Current method reference lists bot-token history scopes for channel types; do not bake in the older blanket claim that public/private thread retrieval necessarily needs a user token. Test the actual token, channel membership, scopes, and thread read. `reply_users` can contain bot IDs, so blind `users.info` calls are unsafe. [Replies](https://docs.slack.dev/reference/methods/conversations.replies/).

Recommendation: prefer events for sustained intake, use bounded history fetches for recovery/context, preserve Slack timestamps as strings, paginate complete unread windows, and advance a high-water mark only after durable enqueue. Handle thread replies explicitly. Respect HTTP 429 `Retry-After` per method/workspace/app. Queue posting near Slack's normal one-message-per-second-per-channel limit; routine agent ACK choruses are both noise and avoidable capacity usage. [Rate limits](https://docs.slack.dev/apis/web-api/rate-limits/).

## Identity, loops, and tokens

Bolt Python's self-event middleware compares authenticated bot user and bot IDs, including events without a user ID. Preserve these protections. Recommendation: allow intended peer IDs explicitly instead of blanket dropping all bot messages; distinguish context delivery from task authority; attach task/correlation IDs, finite hop/turn/reply budgets, and a terminal state. Self suppression alone cannot prevent two different bots from bouncing tasks forever. [Bolt self-event middleware](https://docs.slack.dev/tools/bolt-python/reference/middleware/ignoring_self_events/ignoring_self_events.html).

Bot tokens, user tokens, app-level tokens, and app-configuration tokens have different authority. Keep app configuration credentials with provisioners and use bot identity credentials for the intended installation. A model API key is not a Slack token or execution permission. [Slack token types](https://docs.slack.dev/authentication/tokens/).

When rotation is enabled, implement the supported refresh flow and secure persistence before enabling it in production. Slack documents twelve-hour expiry and replacement refresh tokens; enabling rotation cannot be undone. Recommendation: serialize refresh writes for each installation and test recovery. Do not use a generic manual “replace then revoke old token” recipe for migration to Slack's OAuth rotation: revoking the original token with `auth.revoke` can revoke the authorization and force reinstallation. [Token rotation](https://docs.slack.dev/authentication/using-token-rotation/).

## Current managed routes and boundaries

| Route | Source-confirmed distinction | Recommended record/proof |
| --- | --- | --- |
| ChatGPT dot | Connect Slack from the dot profile. DMs and mentions in channel threads are supported. By default it responds to its owner; owner can direct engagement with others. Adding to a channel does not establish monitoring. | Record contact-method availability, owner, allowed interlocutors, privacy rules, and separately confirmed recurring task if monitoring is requested. |
| ChatGPT in Slack / Codex Cloud | New requests use `@ChatGPT`. Cloud delegation needs an eligible published, workspace-shared environment and required account/repository access. Personal Cloud environments do not qualify. | Record ChatGPT deployment versus dot identity, environment, task account, actual returned task. Do not equate this with the existing local Codex session. |
| Claude Tag | Organization-managed channel work on first-party Team/Enterprise plans; shared configuration and usage billing. | Record organization/channel configuration and spend owner. |
| Earlier Claude Code Slack | Individual Pro/Max path remains only in workspaces not connected to Claude Tag. | Determine actual organization linkage; do not call every older install retired or assume all plans migrate identically. |
| Cursor | Supports explicit repo/environment/model and worker/pool options. Public-channel settings are not a private-channel default solution. | Record actual execution location and target; use explicit supported options and verify resulting task. |
| Grok Team Bot | Managed bot with a dedicated Slack app and Cursor account linking; connected-resource permissions and private/shared memory require their own checks. | Use the Grok/Cursor correction below; distinguish native installation from resource credentials and verify calling-account eligibility and triggers. |
| Grok API-key Slack app | Distinct `@Grok` app with an xAI API key and Slack conversations/tools. | Do not infer full Team Bot or coding-runner capabilities from this install. |

Sources: [Dots messaging](https://learn.chatgpt.com/docs/dots/channels), [ChatGPT in Slack](https://learn.chatgpt.com/docs/third-party/slack), [Claude Tag](https://claude.com/docs/claude-tag/overview), [Earlier Claude Code Slack](https://code.claude.com/docs/en/slack), [Cursor Slack](https://cursor.com/docs/integrations/slack), [Grok Team Bots](https://docs.x.ai/grok-bot/team-bots), [Grok API-key Slack app](https://slack.hooks.x.ai/).

Team Bot setup officially authorizes through Cursor and creates a dedicated per-bot Slack app, separate from the Cursor app. This is the documented relationship. Use [the identity guide](grok-cursor-identity.md) to map the installed account, assistant and worker correctly.

## Model and provider routing

For OpenRouter, the model ID and selected hosting provider are separate choices. Provider fallback defaults to enabled; `provider.allow_fallbacks=false` constrains failover, and `provider.only`/exact provider slugs constrain routes. This is separate from a `models` fallback list or auto-routing. `provider.require_parameters=true` prevents silent unsupported-parameter loss. Recommendation: record model fallback and provider fallback separately; pin when identity/reproducibility/data location matters; verify supported tools and returned provider/model for the actual run. Record relevant data collection/ZDR constraints instead of assuming all endpoints share a policy. [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).

## Public package acceptance additions

Add tests/checklist rows for fast ACK independent of slow work; invalid/stale HTTP signature; duplicate event after restart; ambiguous result-post reconciliation; HTTP 429 backoff; same-message delivery from several app identities; unknown-peer rejection; private-context leakage prevention; finite two-agent handoff; permission denial; actual personal assistant resource access without a repository; requested monitoring confirmed separately; and role-specific capability results (notification, conversational, tool-using, implementation).

For a documentation-only package, these are setup acceptance procedures, not claims that a runtime or every vendor route has been executed. Public CI should validate JSON, internal links, packaging, absence of credentials, and consistency of examples. A full repo fits the existing multi-file skill and lets users version, fork, and contribute fixes.

## Desktop-assisted sessions

User premise: the public procedure should assume authorized desktop access and use it as far as practical. State that up front, while retaining real login/admin/tool-policy gates. Recommended route: when a product has no supported incoming API, an authorized desktop operator can target an existing session through its actual UI. Record application, window/session identity, focused input, intended recipient and task correlation; verify submission and real result before reporting delivery. Model response generation, returned message and actual tool execution are separate proofs. A local desktop that requires login/unlock/awake state is an interactive availability dependency, not an unattended hosted service. Do not invent a stable background wake-up capability from one successful UI handoff. These are operational recommendations, not claims of a vendor-supported automation API. Desktop access alone also does not change whose data a managed shared assistant may disclose.

## Grok/Cursor and Slack Agent correction, October 17, 2026

The initial product list did not adequately explain the overlap. Official [Team Bot documentation](https://docs.x.ai/grok-bot/team-bots) confirms Cursor account authorization with a separate Slack app per Team Bot. [Model documentation](https://prod.cursor.com/help/grok-bot/models) distinguishes managed, unreported Grok Bot models from selectable models in other Cursor runtimes. Scoped inspection of two local projects and installed app metadata corroborated distinct app/session namespaces and parent-to-cloud-worker delegation. It did not establish universal shared memory or identical participants. Use [the identity procedure](grok-cursor-identity.md).

Slack's [agent documentation](https://docs.slack.dev/ai/developing-agents/) explicitly links `assistant:write` to agent features and labeling. [Agent migration](https://docs.slack.dev/ai/migrating-to-agent-messaging/) is substantive and one-way; [token types](https://docs.slack.dev/authentication/tokens/) remain a separate concern. A historical local visual test corroborated APP-to-AGENT configuration, but token survival in one reinstall is not a general guarantee. Use [the app/agent procedure](slack-apps-and-agents.md).

Live dogfooding found that channel invitation and successful posting can coexist with missing private-history scope, and an old healthy status file can outlive its listener. These observations sharpen the subscription acceptance checks; they do not establish an always-on four-agent network. Private setup evidence and model consultations remain outside the public package.

## Participant kinds, October 18, 2026

These were checked against official vendor docs and repositories, read live on 2026-10-18; most pages show no date. Each claim was marked confirmed, corrected, or unverified. Unverified claims stay out of the guides.

- **ChatGPT and Codex:** the former Codex Slack docs URL now permanently redirects to [Use ChatGPT in Slack](https://learn.chatgpt.com/docs/third-party/slack). `@ChatGPT` can delegate repository work to a Codex Cloud task, and `@Codex` is the legacy name. Dots use the same ChatGPT Slack app, and only the owner can direct a dot ([dots channels](https://learn.chatgpt.com/docs/dots/channels), [dots admin guide](https://learn.chatgpt.com/docs/enterprise/dots-admin-guide)).
- **Grok Bot:** desktop and mobile apps, included with paid Cursor plans ([Grok Bot](https://docs.x.ai/grok-bot)). Each Team Bot has its own Slack app and answers DMs, mentions and followed threads; untagged top-level messages need a listener routine. "Posts from Slack workflows and other apps are the exception" to the linked-account rule, billed to the owner ([Team Bots](https://docs.x.ai/grok-bot/team-bots)). Sender rules for personal bots and for Slack-triggered routines are not documented.
- **Muse:** "Muse Wonder Full is available only in Muse Code with a subscription" ([models](https://dev.meta.ai/docs/models)). Meta's October 13 announcement says Muse Wonder "will soon power experiences in Muse," a separate product ([announcement](https://about.fb.com/news/2026/10/introducing-muse-wonder-models/)).
- **Claude:** Claude Tag reads channel top-level messages; a mention guarantees a pickup ([Claude Tag](https://claude.com/docs/claude-tag/overview)). The earlier Claude Code in Slack works on mentions only and is retired in Tag-connected workspaces ([Claude Code in Slack](https://code.claude.com/docs/en/slack)). The Claude Code CLI's channels preview covers Telegram, Discord and iMessage, not Slack ([channels](https://code.claude.com/docs/en/channels)).
- **Cursor:** `@Cursor` starts a Cloud Agent; a later `@Cursor` in the same thread adds a follow-up; `@Cursor agent` forces a new agent ([Cursor in Slack](https://cursor.com/docs/integrations/slack)). Whether it ever replies top-level is unverified.
- **Antigravity and Gemini CLI:** both are coding agents ([Antigravity](https://antigravity.google/llms.txt), [Gemini CLI ACP mode](https://geminicli.com/docs/cli/acp-mode)). An official Antigravity ACP mode is unverified.
- **Hermes and OpenClaw:** self-hosted assistant runners with Slack gateways ([OpenClaw](https://github.com/openclaw/openclaw), [Hermes Agent](https://github.com/NousResearch/hermes-agent)).
- **Slack:** bot posts arrive as message events carrying `bot_id` and `bot_profile`; the docs describe no platform-side bot filter ([bot_message](https://docs.slack.dev/reference/events/message/bot_message/)). Slackbot has `is_bot: false` ([user object](https://docs.slack.dev/reference/objects/user-object/)) and is now described as a personal agent with admin-controlled access ([Slackbot](https://slack.com/help/articles/202026038-An-introduction-to-Slackbot)).
- **Live lab observations, same night:**
  - A Grok Bot routine saw a post from the lead bot, but the @-mention arrived as escaped text flagged as not a mention.
  - The native Cursor app did not launch from a bot's mention.
  - `codex exec` 0.158 recorded approval policy "never" despite other configured policies. Codex's own docs-cited answer: exec has no human approval channel, and per-server `default_tools_approval_mode`, `enabled_tools`/`disabled_tools` or `enabled=false` control MCP tools ([MCP configuration](https://learn.chatgpt.com/docs/extend/mcp)).
