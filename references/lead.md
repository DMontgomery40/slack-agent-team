# The lead

Every team needs exactly one named lead. Without one, nothing happens: each participant waits for someone else to start, assign, or decide.

## Choosing the lead

The user names the lead when pointing an assistant at this skill. If they did not, ask once, before connecting anyone else. This is a required decision, not a preference to infer. Include a recommendation: an agent with strong reasoning, reliable tools, and a working route to receive channel messages without being tagged. Record the lead in the roster (`coordination.lead`) and announce it in the channel.

The lead can change. The outgoing lead posts the handoff top-level in the channel and saves it with the roster; the new lead announces itself the same way.

## Roles by strength (recommended)

Start from each participant's kind ([assistants versus coding agents](participants.md)): assistants take personal, research and account tasks; coding agents take repository work.

Not required, but teams work better when the lead assigns roles by what each model and harness actually does well in this team. For example:

- **Lead/coordinator:** strong reasoning, dependable tools, stays attached to the channel.
- **Implementers:** coding agents with repository access, each claiming its own file area.
- **Reviewer:** a different model family from the implementer, for an independent check.
- **Research:** the participant with the best search and source tools.
- **Personal assistants (dots, Grok bots, Muse, and similar):** persistent memory and personal context; route personal tasks to them.

These are starting points, not fixed assignments. No model gets a restricted role by default. A restriction such as review-only is a choice the user or lead makes for a particular project; record it on that project's roster entry, not as a general rule.

## Listen, and make sure the team can hear you

The lead runs as a persistent session with its own loop: a Codex heartbeat every 5 minutes, or `/loop 5m …` in Claude Code ([listeners.md](listeners.md)). On each wake it:
- reads what's new;
- acts on it;
- stays quiet if nothing changed.

Without the loop, the lead goes silent the moment its turn ends.

A lead that posts as a bot reaches nobody until something delivers its posts. Vendor bots often treat a bot's mention differently from a human's. In an October 2026 test:
- a Grok Bot routine saw the lead bot's post, but received the @-mention as escaped text, so its mention trigger never fired;
- the native Cursor app didn't launch at all from a bot's @-mention.

Before relying on a participant, test it with a real post from the lead's bot. Silence after a lead post usually means nobody received it, not that everyone agreed.

## Channel vocabulary

These short words grew naturally in long-running team channels. They make status scannable for humans and agents alike. The lead uses them and asks the team to use them too.

| Word | Meaning |
| --- | --- |
| **ACK** | The owner received and accepts an assignment or handoff. Only the owner sends it; never infer it from a tag or from silence. "ACK + CLAIM" is common. |
| **CLAIM** | Taking sole ownership of a ticket or scope, naming the ticket, branch, scope and ETA, e.g. "ACK + CLAIM KAN-53, branch `feat/x`, README only, ETA 0.5 agent-hour". |
| **READY** | Ready for review. |
| **PASS** / **FAIL** | The result of a check, with its evidence. |
| **HOLD** | Frozen: nobody merges, amends, or touches it. |
| **BLOCKED** | Stopped, naming the blocker and who owns it. |
| **DONE** | Finished, with evidence. |
| **HANDOFF** | An ownership transfer, with a durable handoff note. |
| **RELEASE** | The owner releases a scope, or approves the next step. |
| **ETA** | An estimate, often in agent-hours. |
| `[ROLE]` prefix | Who is speaking, when one identity serves several roles, e.g. `[PM]`, `[ENGINEERING HANDOFF]`. |

"No ACK needed" at the end of an FYI stops a chorus of acknowledgments. Use a reaction to say "heard". The reference relay adds 👀 automatically.

## Standing instructions for the lead

The setup agent gives the lead this section through its harness's project instructions or its loop prompt, and confirms the lead has read it.

1. **Start your loop.** Check the channel every 5 minutes while you lead, and save the newest timestamp you've handled ([listeners.md](listeners.md)).
2. **Post early and top-level.** As soon as you're a channel member, say who you are (product and model), that you're the lead, and who you can see. Ask the human your setup questions in the channel. Once the team is in, post the roster, the [team rules](team-rules.md), how to address each agent, and what you need from the human.
3. **Be active.** Answer the human promptly. Post short status at meaningful points instead of going quiet, and never post unchanged status.
4. **Use the team.** Assign work rather than doing everything yourself. Start each assignment with the agent's name followed by a request, such as "Codex, run the tests" or "Codex, can you…?". A name alone, as in "Codex, here's your assignment", may not wake it. Name the scope, the expected result and when it's due. In coding projects, every assignment is a [ticket](coding-projects.md).
5. **Don't do your team's jobs.** Once a role has an owner, such as a UI lead, that work is theirs. Don't write it yourself. Your own code work is integration and the areas you've claimed. If an owner is stuck or slow, unblock them or reassign the work out loud in the channel; don't quietly take it over.
6. **Follow up.** Act on READY, PASS, FAIL, BLOCKED and DONE: review, unblock, reassign or accept.
7. **Give shoutouts.** When someone does good work, say so by name and say what was good about it.
8. **Hold weak work accountable.** When work is wrong or incomplete, say what's wrong, show the evidence and say what's needed. Reassign if it keeps happening. Check the evidence before you repeat a teammate's claim as fact.
9. **Keep the tracker and the team context file current.**
10. **Ask the human only for what only they can give,** such as decisions, logins and approvals. Batch those asks into one message.
11. **Hand off before you fill up.** At 75–85% of your context window, write a handoff and hand over to a fresh session of the same role and model. Give the new session the loop: move a Codex heartbeat to it, or start `/loop` there and cancel the old one in Claude Code. Confirm it started real work before you stop.
