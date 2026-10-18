---
name: slack-agent-team
description: Connect and coordinate assistants, existing sessions, dots, and bots through Slack for everyday tasks or project work. Use for onboarding, cross-agent handoffs, or delivery/session failures, not ordinary Slack messaging.
---

# Slack agent team

**Assumption: the user has authorized desktop use for this setup. Use available desktop controls, installed apps, browser, and terminal proactively, alongside connected tools and supported APIs. Complete the authorized setup; pause only at a concrete missing login, MFA, operating-system permission, administrator restriction, or action outside the user's scope.** Desktop access does not override a tool's actual permission controls. The only normal human action is pointing an assistant at this skill; every procedure below is for agents to execute, including installation, subscription changes, and credential setup.

When unstated, infer values from the current account, conversation, existing setup, and authorized shared context. Default owner to the requesting user; preserve existing channel privacy/modes, and make new channels private. Use the user/account timezone before the host timezone, preserve established quiet hours, and otherwise leave quiet hours unset without starting unsolicited schedules. Use existing authorized spend only. For a new custom task without existing limits, use starter bounds of 10 model turns, 6 public replies, 3 handoffs, 1 concurrent task per session, and 15 minutes per bounded task; split larger work into units and adjust within existing authorization. Choose a reachable private setup/memory location yourself and record it; do not ask the human to fill templates. Ask only for a genuinely missing decision that cannot be inferred and materially blocks the requested work.

When reading this file by URL, resolve relative references against `https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/` or obtain the complete repository tree. Follow the selected references yourself.

Connect the assistants the user already uses. A team may be a personal dot and a research bot, several existing chats, a household helper, or a large project with independent workers. A repository, coding role, new workspace, and custom bot are all optional. Preserve existing sessions and selected products/models.

This is a setup and operating skill with templates, not a bundled always-on relay. Produce a verified path from the real sender to the intended participant and back, and name exactly which parts still require a bridge or human operation.

## 0. Bootstrap and onboard

If reached through one URL, obtain a complete readable tree or fetch the linked files against the source base. Verify required references are accessible before using them. Discover the intended existing participants from the conversation and workspace. The setup agent delivers this entrypoint, applicable complete references, and the shared roster/context pointer to each participant through its actual authorized route; the human does not repeat onboarding per bot. Record each participant’s receipt and access gaps. If joining an already configured team, register only the missing participant.

**Done:** one setup owner has the readable package and each intended participant has received the applicable onboarding material or a named access gate.

## 1. Discover the participants

Infer purpose, owners, participants, existing Slack channels, resource access, and current authorization from the conversation and installed environment. Participants may use Hermes, OpenClaw, Codex, Claude, Muse, Grok, dots, or another harness; these are discovery assumptions, not instructions to install new products. Inspect available app integrations and sessions before creating anything. Keep existing channels and active work intact. Read [setup-workflow.md](references/setup-workflow.md) when you need inventory, provisioning, or handover details. When joining a configured team, read its roster and register only your participant/session; coordinate with its setup owner instead of reprovisioning everyone.

For each participant, distinguish product/harness, exact model if exposed, account, visible identity, and actual conversation/session. Discover whether it can read, receive, wake, continue an existing session, reply, and act. Record verified, untested, unsupported, or not applicable for each capability in [team.example.json](assets/team.example.json). Read [interoperability.md](references/interoperability.md) when selecting or diagnosing a participant’s native, desktop, connector, or custom route.

When Grok Bot and Cursor overlap, resolve the actual assistant, model-in-runtime, and delegated worker through [grok-cursor-identity.md](references/grok-cursor-identity.md). When creating tokens or diagnosing APP versus AGENT, read [slack-apps-and-agents.md](references/slack-apps-and-agents.md); a Slack feature, bot identity, credential, and running agent are separate layers.

Before project work, every participant reads applicable context across `.codex/`, `.claude/`, other present project harness directories, and relevant nested instructions. For personal assistance, create a separate private `SHARED_MEMORY.md` and have every assistant read the same revision. Follow [shared-context.md](references/shared-context.md) for boundaries and approved external pointers in both branches. All personal-assistant agents use the relevant [pstack skills](references/pstack.md), regardless of harness; record how each loads the same reviewed source.

**Done:** each requested participant has a named route, owner, capability record, and unresolved gates. A model with the same name is not a replacement for the user's existing assistant and memory.

## 2. Connect the smallest useful workflow

Prefer the product's existing Slack integration or supported session controls. Use desktop/browser setup when that is the available route. A desktop-controlled session is a valid participant; document foreground, login, sleep, and supervision dependencies. Use a custom receiver only where the requested workflow needs one.

Set the audience and purpose for each channel or DM. Keep personal context private unless sharing is authorized. A public skill repository does not imply a public Slack channel. Read [multiple-roles.md](references/multiple-roles.md) when several participants share a harness/model or need separate identities.

Read [notifications.md](references/notifications.md) whenever subscribing a participant or switching all messages ↔ mentions only; apply the actual runtime control and verify positive/negative delivery. Read [credentials-and-lifecycle.md](references/credentials-and-lifecycle.md) when adding credentials or separating temporary projects from persistent personal assistants.

Support Follow conversation, Follow assigned work, Mentions only, and Muted as explicit per-participant/channel preferences where the route permits. Use the requested behavior and the defaults in the notification guide. Separate receiving context, waking a model, replying publicly, and authorization to execute. Preserve useful peer context without an acknowledgment chorus.

For custom routes read [delivery-and-recovery.md](references/delivery-and-recovery.md) and select [manifest templates](assets/README.md). Keep credentials outside the package and distinguish bot, app-level, signing, provider, and provisioning secrets. When a provider claim is uncertain or stale, use [source references](references/research.md) to recheck its current official documentation.

**Done:** one bounded, useful handoff works through the selected path. Expand to the remaining participants without replacing working integrations.

## 3. Make cooperation accountable

Use [handoff.example.json](assets/handoff.example.json) as an optional adapter contract: original sender, recipient, conversation/task identity, authorized scope, context, expected result, deadline/timezone, and reply destination. It is a local design, not a Slack or vendor API schema. Direct peer and coordinator-routed collaboration are both valid; choose based on the number of participants and available controls.

For personal assistance, preserve private calendars/mail and sharing limits, quiet hours, timezone, task expiry, and recurring-task intent. For projects, add resource/repo scope, accountable owners, work isolation where needed, review policy, and artifact evidence. A peer message can supply context without granting new authority. Enforce configured authority in the available runtime/adapter controls.

**Done:** tasks have an owner, finite reply/handoff/spend bounds, completion state, and a cancellation/recovery route. A receipt or queued event is not completed work.

## 4. Verify and hand over

Run applicable checks from [acceptance.md](assets/acceptance.md), including the actual peer/coordinator sender, existing-session continuity, useful tool output, audience isolation, no echo loops, and idle-point recovery. Test live only within the authorized setup; use offline fixtures for disruptive or cross-boundary failure cases. Never interrupt active work to finish a checklist.

Save a redacted roster, preferences, configuration/version references, evidence, operator, and stop/recovery instructions in an agent-selected reachable private setup location, respecting any existing user preference. Keep installed skill files reusable. Mark manual relay, interactive desktop, notification-only, analysis-only, and action-capable routes accurately, with tested surfaces and availability.

Finish with what works, what remains untested or unavailable, and the exact next owner action. Do not call installed apps, prepared templates, or a fresh substitute chat an operational connection to an existing assistant.

**Done:** the requested capabilities have current evidence or named access gaps, the private operating record is saved, and the user has the working destination plus an accurate availability statement.
