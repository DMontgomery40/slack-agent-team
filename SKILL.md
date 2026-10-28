---
name: slack-agent-team
description: Use when setting up a Slack assistant team, reproducing an existing team's setup, or diagnosing an agent that misses channel messages.
---

# Slack agent team

Use the desktop, terminal, apps and connected tools already authorized for the task. Complete setup yourself; bring back only missing decisions or access that requires the user.

For URL reads, resolve relative links against this file's directory at the same Git revision, or clone the repository at that revision.

## 1. Inspect what exists

Find the intended project, channel, lead, participants, installed apps, token references and running sessions. Read the project's instructions and relevant `.claude`, `.codex` or equivalent context. Keep private assistant context within its intended audience.

For each participant, identify how it receives work and how it posts. Reuse working routes and existing logins. An app name, token, channel membership or mention is not evidence that a runtime receives messages. Use [identity.md](references/identity.md) when the layers are unclear.

If the lead or membership is still unknown after inspection, ask for the missing choice. Do not require a new lead selection when the project already has one.

## 2. Connect delivery and delegation

Read [listeners.md](references/listeners.md) before changing message delivery. The observed reference is a Claude Code lead running a Python history watcher through Monitor, with Codex/Muse workers launched directly from task briefs. Preserve an existing working Monitor without adding a recurring model check.

Reproduce the route actually chosen for each participant. A task worker can receive its brief from the lead without having a Slack listener. Treat mention-triggered workers, vendor-managed bots, other harnesses and push transports as separate routes requiring their own verification. Inspect installed CLI help and local settings before invoking a worker; retain the user's model, tools and permission choices.

## 3. Start useful work

Have the lead answer people, assign a concrete scope to an available teammate, review the result and integrate it. Use each participant's established Slack identity. The reference team posts short updates top-level in the main channel; follow the destination project's preferences.

Reuse the project's tracker and ownership conventions. Record only what is needed to resume the work: lead, participants, delivery route, relevant paths, current task and how to stop the processes you added. The [team note](assets/TEAM_CONTEXT.template.md) is optional. For personal teams, keep agreed shared personal memory separate from project context; use shared skills the user has selected through each harness's supported mechanism.

## 4. Verify and hand over

Check an untagged human message reaching the lead, a real delegated task reaching its worker, and the result returning through the expected identity. Read existing evidence first; use a live test within the user's authorized scope. Record what was observed and what remains untested. Fetch full messages when the watcher preview is insufficient.

Document watcher expiry, renewal, missed-history recovery and process ownership. The [evidence record](references/betkalshi-evidence.md) distinguishes the current implementation from historical fallbacks. For an employer deployment or API proxy migration, use [workplace-handoff.md](references/workplace-handoff.md); it describes pending decisions, not implemented enterprise support.
