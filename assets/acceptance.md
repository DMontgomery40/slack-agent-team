# Team acceptance record

Purpose / participant / date / operator: REQUIRED
Route, account, intended session, configuration revision: REQUIRED
Expected capability and availability: REQUIRED

Record PASS, FAIL, PENDING, or N/A with a reason. All checks begin PENDING. N/A is appropriate for a capability the team does not need; it cannot stand in for a failed required capability. Distinguish documentation, offline fixtures, observed live behavior, and repeated/recovery proof. Preserve evidence references and dates, never credentials.

| Check | Evidence | Result |
| --- | --- | --- |
| Identity and audience | Correct account/workspace/app/bot/user/session; permitted destination | PENDING |
| Human round trip | Unique request, receipt/task ID, actual reply | PENDING |
| Peer round trip | Actual peer/coordinator sender, intended recipient, useful result or unsupported boundary | PENDING |
| Session continuity | Authorized harmless nonce planted in the existing session and unavailable in relayed Slack history; follow-up plus session-reference evidence | PENDING |
| Read/receive/wake/continue/reply/act | Separate evidence for each claimed capability and surface | PENDING |
| Useful resource/tool task | Permitted note/calendar/document/action/code task independently checked; repo optional | PENDING |
| Shared project context | Every participant read applicable cross-harness context and same reconciled revision | PENDING |
| Shared personal memory | Authorized participants use same revision, honor a correction, and respect reader/writer boundaries | PENDING |
| pstack across personal assistants | Source/revision/load method per participant; relevant skill used on a bounded task | PENDING |
| Subscription readback | Desired/effective modes, loaded actual control/filter generation, member/grant state | PENDING |
| Positive automatic receipt | Intake evidence before follow-up; nonce readback alone is not push proof | PENDING |
| Negative non-delivery | Mentions/mute filter evidence or safe no-history fixture; silence alone insufficient | PENDING |
| Thread and DM coverage | Separate surface tests and explicit unsupported boundaries | PENDING |
| Audience and authority isolation | Unknown sender/route rejected; safe private-context fixture stays private; permitted tool scope enforced | PENDING |
| Session and model identity | Actual product/session/config; disclosed model/provider and fallback when available | PENDING |
| Desktop interaction | Correct app/window/chat/focus, submitted input and returned result, availability dependencies | PENDING |
| Durable delivery | Fast ACK independent of slow work; duplicate event before/after restart does not repeat task | PENDING |
| HTTP verification | Invalid/stale signature rejected in safe fixture, if using HTTP | PENDING |
| Rate limit and backlog | 429/backoff, complete pagination, explicit initial backlog/thread policy | PENDING |
| Bounded cooperation | Finite peer handoff and terminal state; no self-echo or ACK chorus | PENDING |
| Ambiguous effects | Timeout reconciled before replay; uncertain effects remain visibly uncertain | PENDING |
| Expiry/correction/cancel | Stale or superseded work revalidated; cancellation halts further dispatch | PENDING |
| Restart/reconnect | Idle-point recovery retains/reconciles state without duplicated effects | PENDING |
| Requested recurring work | Real schedule and owner verified separately from channel membership | PENDING |
| Operations | Cost owner/limits, inspect/pause/cancel, retention, rotation/revocation, stop/recover | PENDING |

## Claim levels and applicable checks

- **Planned:** configuration/templates prepared; no delivery claim.
- **One-way:** one actual receive or reply path verified; state which.
- **Verified round trip:** actual intended sender → target session → returned result, with identity/audience/context proof. A peer round trip specifically needs the real peer sender; a desktop relay is labeled as such.
- **Operational unattended:** verified round trip plus automatic receive/wake evidence, supervised availability and recovery appropriate to that route. Hidden intake remains unobservable, not automatically verified.

Core checks are identity/audience, the requested human/peer round trip, capability evidence, useful result, applicable notification modes, and authority scope. Project context applies to projects; shared personal memory and pstack apply to personal assistants. Desktop focus checks apply to desktop routes. Durable delivery, signatures, polling/429 and restart checks apply to the selected custom transport. Recurring-task proof applies only when recurring work was requested. Mark other rows N/A with the reason; do not make a personal assistant pass irrelevant code/HTTP checks.

Final capabilities: REQUIRED
Availability: REQUIRED_HOSTED_INTERACTIVE_DESKTOP_MANUAL_OR_MIXED
Untested/unsupported gates and owners: REQUIRED
Evidence invalidation triggers (configuration/account/scope/session/version changes): REQUIRED
Next useful action: REQUIRED

A prepared template or another session's historic test is not fresh end-to-end proof. Managed products may expose task IDs instead of logs; record that evidence and its limits.
