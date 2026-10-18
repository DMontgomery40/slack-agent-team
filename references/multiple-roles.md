# Multiple agents from the same family or harness

**Organize the team by each agent's job. Multiple agents can use the same family or harness while remaining distinct teammates.** They may use different models, reasoning settings, or the exact same model. This applies to two agents or a larger team.

For example, a project might use one Codex session for QA and another for architecture; two Claude sessions might handle project management and UI; several agents might use the same model for different areas of implementation. These are illustrative staffing choices. Resolve exact available model IDs and reasoning settings during setup.

The harness is the software running the agent, such as Codex or Claude Code. The model is the selected engine within that harness. Neither determines how many jobs or independent teammates the project can define; the chosen runtime must support the required separate sessions and concurrency.

By default, one plainly named app per assistant serves every channel, with a separate runner session per channel ([recommended layout](slack-apps-and-agents.md#recommended-layout-one-app-per-assistant-the-channel-is-the-project)). Only when two seats from the same assistant speak in the **same** channel does each need its own Slack app, bot identity and bot token, named by role rather than by project, and routed to its own runner session. The same underlying harness or provider account may serve several teammates where supported.

| Configuration | Agent A: QA lead | Agent B: architecture lead |
| --- | --- | --- |
| Stable role ID | `qa-lead` | `architecture-lead` |
| Visible Slack name | e.g. "Codex · QA" (role, not project) | e.g. "Codex · Architecture" |
| Harness | Selected harness | May be the same harness |
| Model and reasoning | Selected model/settings | May be different or identical |
| Slack app and bot user | Separate app A and bot-user U IDs | Different app B and bot-user U IDs |
| Bot token reference | `secret-store/PROJECT/qa-lead/slack-bot` | `secret-store/PROJECT/architecture-lead/slack-bot` |
| Actual runner session | Dedicated QA session | Dedicated architecture session |
| Instructions and authority | Test strategy, verification, defect reporting | System design, interfaces, technical decisions within assigned authority |
| Working scope | Assigned test/review artifacts and permitted tools | Assigned design/code artifacts and permitted tools |
| Notifications | Independently configured per channel | Independently configured per channel |

Names and secret references above are illustrative. Resolve real IDs and supported session controls during setup. Do not store raw credentials in this document or project configuration.

The essential binding is **project + agent identity → job + harness/model configuration + actual session + tool/work scope**. Each response must return through the Slack identity for that agent. Route by stable agent IDs, not provider or harness name alone. Keep every agent's conversation state distinct; changing a model does not itself create a new teammate or require a new Slack identity.

## Which credentials are distinct?

- **Slack bot tokens:** distinct because these are separate custom Slack apps/installations. Rotating one app's token does not create another teammate. Changing a message's display name does not create a separate identity.
- **Socket Mode tokens:** if each app uses Socket Mode, give each its corresponding app-level token. A polling relay does not need these.
- **Provider/harness authentication:** use the runner's supported login/account arrangement. Several agents can use the same authorized account where supported; separate Slack identities do not create additional subscriptions, rate limits, or usage allowances. Check the selected runtime's concurrency and account constraints.
- **Session IDs:** distinct conversation state, not authentication tokens. A second Slack token alone does not isolate the model's context, tools, or files.

Sources for the underlying distinctions: [Slack credential types](https://docs.slack.dev/authentication/tokens/), [Slack app/identity configuration](https://docs.slack.dev/reference/app-manifest/). This arrangement is an implementation recipe for a custom relay, not a claim that a managed vendor app exposes its tokens or supports cloning its identity.

## Set it up without duplicating working infrastructure

1. Inventory the existing agents and sessions. Preserve each working identity/session for its intended job; add only the missing teammates.
2. Create one roster entry per agent, keyed by a stable agent ID, even when harness, provider, and model are identical. Record its job, harness, model/reasoning settings, Slack identity, token reference, actual session, instructions, tool scope, and notification preferences. If two agents share a job title, give them distinct agent IDs and explicit assignments.
3. Configure the existing receiver to route each identity correctly. Leadership and assignment authority belong to explicitly designated agents; another agent using the same model or harness does not inherit them.
4. Preserve shared project knowledge intentionally through explicit documents or delivered channel context. Keep role conversation state separate. Use separate worktrees for concurrent edits where appropriate; session separation alone is not filesystem isolation.
5. Verify every route through the real runtime. Deliver different harmless job-specific context to each session and confirm correct follow-ups and response identities. Check that changing one agent's channel preference leaves the others unchanged. Test an authorized handoff and finite completion without a reply loop. Record account/quota-gated agents as pending.

For a **vendor-managed Slack app**, use its supported role/session features and document any identity limitation. Do not assume its hidden bot token is available or that registering another custom app automatically connects to its managed runtime.
