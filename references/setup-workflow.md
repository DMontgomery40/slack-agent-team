# Setup reference

Use the procedure in [SKILL.md](../SKILL.md). Consult the relevant section here for inventory, custom provisioning, or handover details; route-specific procedures own their own rules.

## Inventory and join an existing team

Inspect purpose, human owners, current roster, Slack workspace/channel IDs and audiences, product accounts, existing conversations/sessions, tools, listeners/schedulers, and relevant resource access. Use configured metadata and current conversation to fill planning records yourself. Preserve working identities and inspect an existing coordinator’s state before adding infrastructure.

For a participant joining an established team, read the shared roster and context revision, identify its own real account/session, and register its capabilities and preferred channel modes through the existing coordinator/control. Configure only the missing route for that participant. Verify one handoff with an existing member; do not create a second team or receiver.

Use [team.example.json](../assets/team.example.json) as the generic record, [personal.example.json](../assets/personal.example.json) for daily assistance, or [project.example.json](../assets/project.example.json) for optional code roles. These are examples to adapt, not forms the human must complete. Use null with a reason for inapplicable or vendor-hidden values. A repository is optional.

Distinguish stable participant ID, app ID, bot user ID, bot ID, account, model, and session. Slack app, bot, and user identifiers serve different purposes. Preserve IDs returned by supported APIs rather than deriving them from display names.

## Custom identity provisioning

For credential ownership and exact temporary/persistent procedures, read [credentials-and-lifecycle.md](credentials-and-lifecycle.md). Reuse a correctly scoped existing app. Otherwise select the [manifest](../assets/README.md), validate through Slack’s UI/API, install into the intended workspace, and authorize required scopes through the available supported flow. Compare effective grants after changes; editing a template does not change an installed token.

Check authenticated identity, intended channel membership, and appropriate allowed read before binding the session. Credential capture goes directly to the selected external secret store, not into prompts, screenshots, logs or repository files. Separate custom transport setup from managed products, which own their own account/login flow.

Use [notifications.md](notifications.md) to configure and prove subscription behavior. Read [delivery-and-recovery.md](delivery-and-recovery.md) only when a custom receiver/adapter needs durable intake, routing, replay and recovery controls.

## Context and resource checks

Read [shared-context.md](shared-context.md) for cross-harness project context or personal shared memory. When the team includes personal assistants and the user wants pstack (recommended, optional), follow [pstack.md](pstack.md) to load the actual relevant dependency files across those participants. Check artifact permissions before forwarding content; an accessible link for one agent is not shared access for everyone.

Validate useful work against the role’s real resources: a permitted note/calendar/document read, a plan from shared constraints, a review, or an authorized disposable code edit. Prefer exact evidence over generic acknowledgments. Independent tool policy enforces review-only roles where required.

## Handover record

The agent selects an existing reachable private location, respecting stated preferences. Store the redacted roster, real configuration/version references, tested capabilities, preferences, evidence, operator, cost limits, inspect/pause/cancel/recovery controls, and retention/deletion policy. Record desktop login/lock/sleep dependencies and unsupported surfaces explicitly.

For rotation, refresh, project retirement, or personal-assistant continuity, use the single procedure in [credentials-and-lifecycle.md](credentials-and-lifecycle.md). Shared installations and unrelated sessions remain available to their existing users.
