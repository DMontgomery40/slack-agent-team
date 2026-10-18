# The lead

Every team needs exactly one named lead. Without one, nothing happens: each participant waits for someone else to start, assign, or decide.

## Choosing the lead

The user names the lead when pointing an assistant at this skill. If they did not, ask once, before connecting anyone else. This is a required decision, not a preference to infer. Include a recommendation: an agent with strong reasoning, reliable tools, and a working route to receive channel messages without being tagged. Record the lead in the roster (`coordination.lead`) and announce it in the channel.

The lead can change. The outgoing lead posts the handoff top-level in the channel and saves it with the roster; the new lead announces itself the same way.

## Roles by strength (recommended)

Start from each participant's kind ([assistants versus coding agents](participants.md)): assistants take personal, research and account tasks; coding agents take repository work.

Not required, but teams work better when the lead assigns roles by what each model and harness actually does well in this team. For example:

- **Lead/coordinator:** strong reasoning, dependable tools, stays attached to the channel.
- **Implementers:** coding agents with repository access, each in its own worktree.
- **Reviewer:** a different model family from the implementer, for an independent check.
- **Research:** the participant with the best search and source tools.
- **Personal assistants (dots, Grok bots, Muse, and similar):** persistent memory and personal context; route personal tasks to them.

These are starting points, not fixed assignments. No model gets a restricted role by default. A restriction such as review-only is a choice the user or lead makes for a particular project; record it on that project's roster entry, not as a general rule.

## Make sure the team can hear you

A lead that posts as a bot reaches nobody until something delivers its posts. Adding bots to a channel does not start a listener. Vendor bots often treat a bot's mention differently from a human's. In an October 2026 test, a Grok Bot routine saw the lead bot's post, but the @-mention reached it as escaped text flagged as not a mention, so its mention trigger never fired; only its keyword trigger did. The native Cursor app did not launch at all from a bot's @-mention. Test each vendor bot with a real post from the lead's bot. Before relying on any participant, confirm it receives the lead's posts through one of these routes:
- a relay that treats the lead's posts as assignments ([routing](delivery-and-recovery.md#routing-authority-and-loops));
- a vendor route that accepts bot senders;
- the human, as a labeled relay of last resort.

Record the route for each participant. Silence after a lead post usually means nobody received it, not that everyone agreed.

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

"No ACK needed" at the end of an FYI stops a chorus of acknowledgments. Prefer a reaction for "heard": a relay can add 👀 automatically when a seat receives a message addressed to it, so nobody posts a bare ACK for thanks or an FYI.

## Standing instructions for the lead

The setup agent gives the lead this section as standing instructions through its harness's project instructions, its relay seat prompt, or a pinned onboarding brief. Confirm the lead has read it. A relay seat marked as lead receives it with every prompt.

1. **Announce yourself.** On day one, after the first-run discovery in [SKILL.md](../SKILL.md) step 1, post top-level: who you are (product, model, session), that you are lead, the team rules, the roster and how to address each participant, and what you need from the human.
2. **Be active in the channel.** Answer the human promptly. Post short status updates at meaningful points while you work instead of going quiet. Post top-level; follow the [thread policy](notifications.md#thread-policy-no-threads-by-default).
3. **Use the team.** Assign work rather than doing everything yourself. Each assignment names the owner, scope, expected result, and when it is due. For coding projects, every assignment is a [ticket](coding-projects.md).
4. **Give shoutouts.** When someone does good work, say so by name and say what was good about it.
5. **Hold weak work accountable.** When work is wrong or incomplete, say what is wrong, show the evidence, and say what is needed. Reassign if it keeps happening. Check evidence before repeating a teammate's claim as fact.
6. **Keep shared state current.** Update the task tracker and shared context, and post the new revision when it changes.
7. **Ask the human only for what only they can give,** such as decisions, logins, and approvals. Batch those asks into one message.
