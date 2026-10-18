# How each agent hears the channel

Adding a bot to a channel doesn't make it read the channel. Each participant needs something that delivers new posts to it. For each participant, use the first route below that works. Then record the route in the setup record and test it with a real post.

## 1. Its own loop: agents that keep a session

Use this whenever possible. The agent keeps its full context and memory between wakes. The lead always runs this way.

On each wake, the loop does the same four things:
1. Read channel messages newer than the timestamp it saved last time.
2. Act only on what's new for it: answer, take an assigned task, follow up.
3. Stay quiet when nothing changed. Never post unchanged status.
4. Save the newest timestamp it processed.

Each agent reads and posts with its own bot token, through a small script with two commands, `history` and `post`. The script:
- reads the token from a private file (mode 600) outside any repository;
- checks the bot identity with `auth.test` before posting;
- refuses any channel outside the team's channels.

**Codex desktop app**
- Attach a heartbeat automation to the agent's chat that runs every 5 minutes.
- Create it with the app's automation tool. Editing the automation's file on disk doesn't change the running schedule.
- Keep one heartbeat per role. When a new chat takes over, move the same heartbeat to it rather than creating a second one, and stop the old chat coordinating.

**Claude Code interactive session**
- Run `/loop 5m <the loop prompt>` in the session.
- Loops fire only while the session is open and idle.
- A fixed-interval loop expires after 7 days, so re-arm it weekly.
- `--resume` restores unexpired scheduled tasks.
- To stop a loop, ask Claude to cancel it, or run `CronDelete <id>`.
- For faster pickup during active work, a Monitor command can print each new message as it arrives. Each Monitor watch ends after at most 30 minutes, so re-arm it.

Sources, checked October 18, 2026: [scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks), [Monitor](https://code.claude.com/docs/en/tools-reference#monitor-tool).

**Other harnesses** (Muse Code, Hermes, OpenClaw and others): use the harness's own scheduler, or a small watcher process that prints new mentions into the running session.

**Cadence:** the lead wakes every 5 minutes. During active work, every agent reads fresh history at least every 2 minutes. Polling isn't instant, so tell the user how long pickup can take.

## 2. Vendor Slack bots

Vendor bots use their own triggers: ChatGPT dots, Claude Tag, Grok Bot routines and the Cursor app ([participants.md](participants.md)).
- Many vendor bots treat a bot's @-mention differently from a human's. Test each one with a real post from the lead's bot.
- Record exceptions, such as a bot that only replies in threads. The lead re-posts those results top-level.

## 3. A bridge or the relay: agents that can't keep a session

For headless CLIs and ACP agents, a small always-running process listens to the channel on the agent's behalf and runs it with each message.

**Mention bridge, for one agent**
- Listens over Socket Mode and wakes the agent when it's mentioned.
- Resumes the same session each time, so the agent keeps its context.
- Posts the reply top-level. A reply of `NO_REPLY` isn't posted.
- Skips duplicates by channel and timestamp.
- Runs as one process per agent, enforced with a file lock.
- On a failed delivery, stops and lets launchd restart it, without replaying the message.

**[Reference relay](../relay/README.md), for several agents in one channel**
- Reads the channel by polling, or by Socket Mode.
- Wakes each agent when it's named with a request ("Codex, run the tests") or @-mentioned.
- Keeps one session per agent per channel.
- Enforces the daily turn limit and the idle pause.

**Permissions:** a relay seat runs headless, with nobody to approve anything. If the user runs a harness without approvals, set `"yolo": true` on its seat ([relay README](../relay/README.md)), so the seat can edit files and run commands the way the user's own sessions do.

**Socket Mode limit:** Slack delivers each event to only one of an app's open connections. If two processes use the same app token, they split the events between them. Run one Socket Mode listener per app, and have any other listener on that app poll instead.

## Who starts work

- The human and the lead assign work. The lead's posts count as assignments.
- Peers ask each other for help by mention. New scope, settings, credentials and permission changes still come from the human or the lead ([team rules](team-rules.md)).
- An agent never wakes on its own posts.
- Run the lead as a persistent session with its own loop, not as a relay seat. If the relay lists the lead, mute that seat (`control.py set <lead> muted`). The lead's bot stays trusted, and only one process answers as the lead.

## Availability

Local listeners only work while the computer is awake and logged in and the app or terminal is open. Note in the setup record which agents stop when the computer sleeps.
