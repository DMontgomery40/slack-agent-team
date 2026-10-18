# Final independent reviews and disposition

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
