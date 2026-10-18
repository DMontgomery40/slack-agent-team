# Coding projects

Defaults for teams where agents write code. Each default can be turned off; record the choice in the roster's `coordination` block. These do not apply to purely personal-assistant teams.

## Jira as the task source of truth (on by default)

Slack is good for conversation and bad as a task database. A ticket board gives every agent one small, current record to read, instead of each agent rereading long shared Markdown or text files to work out who owns what. In the skill author's experience it is noticeably more token-efficient and keeps work moving. Strongly recommended for this kind of setup.

Agent-executed setup:

1. Reuse the project's existing tracker if it has one (Jira, Linear, GitHub Issues). Otherwise create a free Jira Cloud site with one Kanban project. Account sign-up, terms acceptance, and OAuth consent are the user's to approve.
2. Connect each coding agent through the Atlassian remote MCP server (`https://mcp.atlassian.com/v2/mcp` when this was written; recheck the current URL in Atlassian's docs) using that harness's own MCP configuration and OAuth sign-in. Never copy one agent's credential into another's configuration. If a participant cannot connect, the lead includes that participant's ticket details in its assignment message and records the gap.
3. Every ticket names its owner seat, scope (files or area), acceptance criteria, an estimate, dependencies, and an evidence link once work is done. Use these statuses: Ready → Doing → Review → Blocked → Done.
4. The lead creates and maintains tickets. Owners move their own tickets and attach evidence. Slack posts reference ticket keys instead of restating ticket contents.

**Turning it off:** tell the setup agent or lead "no Jira", or set `coordination.task_system` to `{"kind": "none"}`. Tasks then live in the lead's top-level channel posts plus one shared task file, and agents should expect to reread more context.

## Fresh session at 75–85% of the context window (on by default for coding agents)

Long sessions degrade as they fill. When a coding agent reaches 75–85% of its context window, it writes a handoff (ticket states, branch and worktree, what is done, the next step, open risks) to the tracker or its handoff file. It then continues in a fresh session that reads that handoff first. The lead notes the rollover in the channel.

If a harness does not report context usage or cannot start a fresh session, record "not supported" for that participant; it is not a blocking failure. This does not apply to persistent assistants such as dots, Grok bots, or a Muse personal assistant, which manage their own context.

A relay that resumes the same session for every message should track the context usage each CLI reports and roll the seat over at the threshold, giving the new session a handoff summary.

## One writer per working copy

Each concurrent writer gets its own git worktree or clone and branch. Never point a relay seat at the operator's live checkout. The lead, or a named integration owner, merges and runs the combined checks once on stable work.
