# Team rules

These rules come from multi-agent projects that ran for days. The lead puts them in the team context file, and every agent follows them. The user's direct instructions outrank this file.

## Talking

- **Slack is the record.** Trackers and files mirror it; they don't replace it.
- **Post top-level.** Please don't reply in threads; they confuse agents and people. Read old threads as evidence. Some vendor bots only answer in threads, so the lead re-posts their results top-level.
- **Tag the agents you need.** A mention is how an agent gets woken. Tag the human only when you need a decision, a login, an approval or an answer that only they can give. Never post only "waiting on <human>"; say exactly what you need and why.
- **Don't post unchanged status.** End an FYI with "No ACK needed", and use a reaction to show you heard something.
- **Use the [channel vocabulary](lead.md#channel-vocabulary):** ACK, CLAIM, READY, PASS/FAIL, HOLD, BLOCKED, DONE, HANDOFF, RELEASE, ETA.
- **When one bot identity serves several roles,** start each post with the role, for example `[PM]` or `[UI]`.

## Ownership

- **One accountable owner** per ticket and per file area, and that includes the lead: the lead doesn't write code in an area someone else owns. Claim the area in the channel before editing it, and don't redo work that's already finished.
- **One active implementation task per agent.** Reviews and unblocking can run alongside it. Finish or hand off before taking the next task.
- **Help a teammate who asks.** New scope, settings, credentials and permission changes come from the human or the lead.
- **Product decisions can go to a vote** if the team wants: one vote per agent, two matching votes carry, and a three-way split goes to the human.

## Pace

- **Estimate in agent-hours** (0.25, 0.5 or 1), and split anything bigger into pieces you can check on their own.
- **Standup:** at the start of each active hour, post a short standup with five things:
  - the ticket;
  - the evidence so far;
  - the next outcome;
  - the time remaining;
  - any blocker, with its owner.
- **Raise a blocker within five active minutes.** Name the exact failed action, the evidence, the owner and the next step.
- **Review requests get an owner quickly.** A missed response is escalated, never treated as agreement.

## Done

- **Done means the outcome was observed,** with evidence. Say what kind of evidence it is: a local test, CI, a simulator, a real device, or a real-world check.
- **One bounded review** against the acceptance criteria and real defects. Verify each fix, and park speculative improvements.
- **Keep private coordination out of Git:** credentials, personal data and session details stay out of the repo.
- **Nothing paid, physical or permission-changing runs from a heartbeat** without the human's explicit yes. That includes purchases, printing or shipping, and access grants.
