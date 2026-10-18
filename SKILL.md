---
name: slack-agent-team
description: Connect a user's assistants and coding agents as one team in a Slack channel, with a named lead, per-agent listeners, and team rules taken from long-running setups. Use for team setup, adding a channel or agent, or fixing an agent that doesn't hear the channel; not for ordinary Slack messaging.
---

# Slack agent team

**Assumption: the user has authorized desktop use for this setup. Use installed apps, browser, terminal, desktop controls and connected tools to do the work yourself. Stop only at a concrete barrier, such as a login, MFA, OS permission or admin approval that only the user can give.**

The human does two things: points you at this skill and names the lead. Everything else is yours.

When reading this file by URL, resolve relative links against `https://raw.githubusercontent.com/DMontgomery40/slack-agent-team/main/`, or clone the repository.

This skill copies setups that have run real projects for days. Don't add rules, gates or ceremony that they didn't have. Agents run the way the user runs them, including autonomous modes, with their normal tools and MCP servers. Restrictions are opt-in, per agent, when the user asks for them.

## 1. Lead first

If the user didn't name a lead, ask once and recommend one: the strongest coding agent on this computer for a coding project, or the main personal assistant for a personal team. Give the lead [lead.md](references/lead.md).

The lead works in Slack, not just in its terminal. As soon as it's a channel member, it posts top-level: who it is, that it's setting the team up, and who it can see. It asks the user its questions in the channel too.

## 2. Find the team and get everyone in

1. **List every assistant you can find:**
   - Slack apps and bots in the workspace (`users.list`);
   - local CLIs and desktop apps;
   - existing sessions.

   Classify each one as an **assistant** or a **coding agent** ([participants.md](references/participants.md)). Slackbot is neither kind; don't invite or assign it.
2. **Show the user the roster:** "Here's who I can see. Who should I add or leave out, and did I miss anyone?" Carry the user's original request word for word into every agent's onboarding, so the user never repeats it.
3. **Give each assistant one plainly named Slack app,** named for the product: "Codex", "Claude Code", "Muse Code". Never use a project name. Reuse existing apps, and retire duplicates ([slack-apps-and-agents.md](references/slack-apps-and-agents.md)). When Grok Bot and Cursor overlap, read [grok-cursor-identity.md](references/grok-cursor-identity.md).
4. **Invite every participant yourself** with `conversations.invite`. Private channels need `groups:write.invites`; public channels need `channels:write.invites`. Confirm with `conversations.members`.

## 3. Make sure every agent hears the channel

Being in a channel doesn't make an agent read it. Give each participant a listener, following [listeners.md](references/listeners.md):
- **The lead and any agent that can hold a session** run their own loop. In Codex, that's a heartbeat automation every 5 minutes. In Claude Code, it's `/loop 5m …`.
- **Vendor bots** use their own triggers.
- **Agents that can't keep a session** get a bridge or the [reference relay](relay/README.md).

Then test every route with a real post. A bot's @-mention isn't always delivered as a mention.

## 4. Set up the shared record

- **Slack is the conversation record.** Everything else mirrors it.
- **Coding projects:** use a Jira board by default, or the project's existing tracker. Also hand off to a fresh session when a coding agent's context is 75–85% full ([coding-projects.md](references/coding-projects.md)). The user can say "no Jira".
- **Team context file:** write one short file every agent reads, from [TEAM_CONTEXT.template.md](assets/TEAM_CONTEXT.template.md). It covers what the channel is for, the roster, how to address each agent, where things live, and the [team rules](references/team-rules.md).
- **Personal teams:** keep a private `SHARED_MEMORY.md` ([template](assets/SHARED_MEMORY.template.md)). Until every assistant has read it, report shared memory as not set up.
- **pstack:** offer [@poteto's pstack](references/pstack.md) to personal assistants as an optional shared skill set.

## 5. Start the work

1. The lead posts its announcement ([lead.md](references/lead.md)) and assigns the first real task by name.
2. Check that the task comes back through the channel.
3. Save a private setup record outside any repository: roster, apps, token file locations, listeners, how to stop each one. Also save a copy-paste undo script.
4. Tell the user three things:
   - what works;
   - what doesn't work yet;
   - the one thing only they can do next, if there is one.
