# Independent reviews and disposition

Review records below describe particular snapshots. They are not blanket approval of later edits or proof of every live integration.

## Initial publication review

October 17, 2026. Both reviewers received all eleven user instructions verbatim, the complete then-current package, and a source-pinned architecture comparison with Matt Pocock’s skills. Reviews ran without tools or external mutations. This record summarizes design review and subsequent fixes; it does not claim live Slack interoperability tests or model approval of an unchanged final snapshot.

- **Muse Code Wonder Full:** `muse-wonder-full-1.0`, `xhigh`, completed headless review. In addition to an earlier general review, this final pass explicitly reviewed channel subscription switching, evidence of delivery, credential lifecycle, every added user requirement, and the full package.
- **Claude Opus 5.5:** invoked with `claude -p --model claude-opus-5-5`; completed successfully and reported `claude-opus-5-5` in model usage. Reviewed the same requirements, package, and architectural comparator.

## Changes from the reviews

| Finding | Disposition |
| --- | --- |
| Single-link bootstrap did not carry onboarding to other participants | Entry point now requires a readable tree and agent-delivered onboarding; README gives a raw entrypoint URL and an agent-fetchable archive. |
| Two overlapping setup procedures | `SKILL.md` is the sole procedure; setup reference now holds conditional inventory/provisioning/handover details. |
| Assigned-work default lacked routing semantics | Notification guide defines authorized targeted mentions/structured handoffs and registered-task follow-ups. |
| “Readback” was underspecified | Added actual evidence by custom, managed, desktop and polling route; planning files never count as loaded runtime state. |
| Follow-up nonce could falsely prove subscription by fetching history | Requires pre-query intake evidence; hidden intake is explicitly receive-unobservable. Negative tests need intake/filter evidence or a suitable safe fixture. |
| Subscription records drifted across templates | All participant examples now use the same `subscriptions[]` object with desired/effective state, attention policy and evidence. Validator checks structure/recipient consistency. |
| Human-account desktop post could masquerade as peer delivery | Explicitly separates desktop relay from native peer activation and preserves actor attribution. |
| Temporary/persistent credential policy was absent from structured records | Added consistent `credentials[]`, inventory template, ownership/installation/refresh/retirement fields, and explicit new-workspace installation semantics. |
| Hosted assistants could not read local memory/pstack pointers | Agent chooses a reachable store or delivers full relevant contents; revision receipts and per-task refresh describe actual accessibility and persistence. |
| Personal memory update propagation missing | Serialized writer bumps revision, delivers scoped changes, collects read/use receipts and marks stale readers before dependent work. |
| OpenClaw absent from one context list | Unified project-root harness inventory and validation, including Hermes and OpenClaw. No new connectors added. |
| pstack revision/closure/persistence ambiguous | Pinned default with explicit team revision adoption, dependency-tree inventory, known gaps and persistence records; hosted model selection can be N/A. |
| Templates could trigger an unnecessary human interview | Agent-inferred identity/timezone/location/preferences, finite starter task bounds and existing-authorized-spend defaults. REQUIRED marks what the agent resolves, not a human questionnaire. |
| Per-entry memory approval could be inferred | Entries use user-sourced facts under existing sharing/write authorization; no additional per-entry ceremony. |
| Acceptance imposed irrelevant engineering checks on personal assistants | Added claim levels and route-specific applicability; unobservable delivery cannot become unattended readiness. |
| Review documentation was stale | This dated combined record supersedes the initial review’s coverage claims. |

Some reviewer suggestions were adapted rather than copied literally: managed products expose different amounts of configuration, so readback is checked rather than assumed universally hidden; Slack scope changes follow the installed product’s actual reauthorization flow; no fictitious universal mode command is advertised; human approval gates are not added beyond real authorization/access needs; a static list is not claimed to prove every pstack workflow’s transitive closure.

The applied package was revalidated for skill metadata, local references, JSON syntax, shared planning shapes, pstack revision consistency, harness inventory and common accidental-publication patterns. Operational acceptance still belongs to the assistant performing a real setup.

## Lab revision: Grok/Cursor and APP/AGENT, October 17, 2026

The user requested a real Slack discussion and evidence from the installed machine and two existing project setups. Both Muse Code Wonder Full (muse-wonder-full-1.0, xhigh) and local claude -p Opus 5.5 reviewed the full candidate, all eleven original instructions, the latest correction verbatim, local and official research, and the same Matt Pocock comparison. Their actual outputs were relayed into the private lab under explicit fresh-review/coordinator-relay attribution. The existing Grok-in-Cursor project session was also consulted; native Grok Bot automation and Cursor Slack Cloud Agent runs replied independently. These are different sessions/routes, not four interchangeable persistent chats.

### Findings applied

- Replaced the obsolete mixed-brand caution with the documented Cursor authorization/per-Team-Bot app relationship; added explicit native Cursor launcher, parent/worker, automation-child and selected-model versus managed-model distinctions.
- Distinguished inbound integration from outbound posting identity, shared account from shared memory, and decision seats from visible app counts. Added optional identity/health records consistently across templates.
- Separated Slack app, installation, bot user, bot/app-level credentials, Agent experience and runtime. Explained one-way migration and current feature/scopes without inventing an agent-token type or assuming token survival.
- Aligned the polling template with private-channel defaults, led mode-change examples with private-channel coverage, and required reads with the actual receiver credential. Metadata and history scopes are checked by method.
- Added receiver freshness, actual native trigger predicates, keyword versus exact-mention tests, and pre-model own-message filtering to the acceptance guidance. A missing native receipt export remains a limitation.
- Corrected the architecture description, default subscription example, duplicate default policy, role-table typo and personal helper name; added final-step completion criteria and explicit agent ownership of templates. Clarified pstack applies to mixed personal/project roles too.
- Extended the publication scanner to app-level and rotating Slack credentials; positive synthetic patterns and harmless-prefix negatives passed.

Suggestions were evaluated rather than copied indiscriminately. Temporary project ownership does not mean a special temporary token type; persistent assistants still need refresh/rotation. Notification modes may share app event coverage while differing in recipient filters. A scope error on private metadata does not establish that private history also fails. These distinctions were returned to the discussion.

### Live evidence and limits

A private lab was created, with seven existing bot identities and the human owner. Codex authenticated and posted under its bot identity. Its actual private-history read failed with missing_scope, while the separately authorized connector read the lab. Existing project listener status was hours old and was not restarted for this review.

The existing personal bot replied through an automation child and reported a saved Cursor-account keyword/mention routine as intake, with a separate custom posting credential. It corrected its own initial metadata-scope inference after checking actual grants/history. Native Cursor mentions launched fresh Cloud Agent runs; one run reported that its source-channel visibility did not extend to the different private lab. Observed posts prove those reply paths; reported run payloads provide attributed intake evidence, not an independent export of vendor receiver logs.

A Codex-bot direct mention did not produce a reported matching native routine wake. The bot instead reported waking from an incidental keyword in another reviewer's post. Thus keyword-triggered peer intake and strict bot mentions are not conflated; all-message following and unattended four-agent operation were not established. The local model reviews and the existing project model consultation used explicit coordinator mediation. No existing project subscription, relay service, or app feature was changed to manufacture a passing result.

Private transcripts, account/session identifiers, and credential references remain outside this public package. The public changes generalize the observed failure modes; validation of a specific installation remains the setup agent's work.

### Verification after fixes

Both exact requested models completed a second full-package verification with every original instruction, the latest correction, the Matt Pocock comparison, prior findings and actual lab evidence supplied again. Local Claude Opus 5.5 returned **PASS for publication as a bounded setup skill**. Muse Code Wonder Full returned **PASS with no remaining substantive blockers**. Both explicitly excluded certification of all-message following or unattended four-agent operation. Their real results were returned to the same lab through the labeled coordinator route.

Two nonblocking Opus wording suggestions were then applied: the managed-route table now distinguishes native installation from connected-resource credentials, and acceptance explicitly labels vendor-reported run payloads as attributed evidence. This verification record was appended afterward. Package validation and skill metadata validation passed; live installation limits above remain unchanged.
