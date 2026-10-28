# BetKalshi evidence, 28 October 2026

This is a dated inspection of the setup, not a claim that every integration in earlier versions worked. Private transcripts, actual Slack IDs, credentials and filled setup records are excluded from this public repository. The accompanying private audit index maps the source labels below to exact files and line numbers for the owner to inspect.

## Original scope and where the package drifted

**E1 — original human requests, 15 and 17 October.** The original request asked for research and a repeatable skill/workflow based on Scan-to-Make. It explicitly said the documentation space was not intended to become a separate application. Later requests asked for a public package, broader assistant support, shared project context, personal shared memory and configurable notifications. They did not establish that every proposed integration actually worked.

The first public [package commit](https://github.com/DMontgomery40/slack-agent-team/commit/bba2e1b6507c7331f45fdb1d4032b785332e87e9) added 2,399 lines across 32 files, including large project/personal JSON configurations and delivery/recovery policies. A later [relay commit](https://github.com/DMontgomery40/slack-agent-team/commit/41cd80669f855b184f81862090b0c508fdae898a) added a custom runtime. Claude's subsequent [simplification](https://github.com/DMontgomery40/slack-agent-team/commit/5e893d018cf886b43dd2675db2ae0de6c621f915) removed substantial material but retained a five-minute loop as the default lead mechanism.

**E2 — baseline package at 252fe08.** A read-only application of the old skill to today's setup found that it would introduce a redundant model loop, worker listeners/relay, Jira provisioning and fixed process rules. The source documents themselves make these instructions explicit. The old package reported 133 offline tests with one skipped; that did not prove its defaults matched the live channel.

## Current receiving mechanism

**E3 — live source and process.** `work/lead-tools/watch.py` in the project checkout reads `conversations.history(limit=30)`, conditionally reads recent thread replies, deduplicates by timestamp, skips the lead's own messages and join/bot-add notices, prints a preview and sleeps 20 seconds. Its SHA-256 at inspection is recorded in the private index. The process was running beneath the interactive Claude lead at inspection.

**E4 — current lead transcript.** The session repeatedly invokes `Monitor` with that command and `timeout_ms=1800000`. Actual Monitor notifications contain untagged human messages, including two on 28 October at 18:20:43 UTC and 19:25:08 UTC. The matching lead replies appear in Slack 20.1 and 39.8 seconds later. These particular input-to-session receipts establish delivery independently of reply timing.

The watcher makes Slack API calls; it does not invoke a model on every check. Monitor supplies new output to the existing session. The transcript also records Monitor renewals. There is no evidence here of a Socket Mode receiver powering this current route. [Anthropic's current documentation](https://code.claude.com/docs/en/tools-reference#monitor-tool) describes the observed Monitor behavior.

## The welcome examples

**E5 — historical lead transcript and Slack history.** On 24 October a member joined at 17:14:16.930 UTC and Claude welcomed them at 17:14:37.082 UTC (20.2 seconds later). The transcript traces this to a scheduled five-minute history check: the history read saw the join, then Claude resolved the member and posted the welcome. A later entry explicitly says the watcher did not report the join and the five-minute check caught it.

On 26 October, another join was seen in a scheduled history read. Claude did not immediately greet the person. A human later explicitly requested the welcome, and Claude posted it at 18:02:58 UTC.

These are evidence of a **historical Monitor plus scheduled-check combination**, and of a human-requested greeting. They do not establish push delivery of joins or the current scheduler state. Today's watcher still filters joins.

## Workers and identities

**E6 — worker launch records and results.** The lead transcript contains actual Codex and Muse CLI task invocations with written briefs and working directories, including research and review runs. The recorded commands select models and effort at invocation time; those selections are local observations, not this package's defaults. Channel posts and resulting files corroborate work returning through distinct identities.

No active independent mention receiver for today's Codex/Muse task workers was established by this inspection. Older relay files, credentials and channel memberships are not proof that such a receiver is currently running. The old BetKalshi relay's health record is dated 17 October; it is not current health evidence.

**E7 — fresh read-only Slack checks.** `auth.test` succeeded for each of the three existing bot credentials and returned distinct bot/user identities in the same workspace. The lead token could read the intended public channel and was a member. No credential values were printed. These checks establish identity/access, separately from runtime delivery.

## What the portable helper changes

[scripts/slack.py](../scripts/slack.py) generalizes the observed watcher and post helper. It preserves the 20-second default, first-read seeding, local timestamp deduplication, thread window, join/self filters and 600-character previews. It uses environment configuration rather than project paths/IDs and combines the small tools behind one command.

It records an empty initial read as an initialized baseline, and additionally checks Slack `ok` responses, backs off its watch loop for HTTP 429 `Retry-After`, lets top-level intake continue when a thread cannot be read, writes the state through a temporary file, checks identity at startup, accepts posts on stdin, and prints bounded error codes. These are new helper adaptations, not claims about the deployed script. It does not add a model runner, queue, database, scheduler, role restriction or quota.

Validation consists of offline behavior tests plus read-only `auth`, `history` and one-shot watcher checks with existing credentials and fresh private state. No test messages or new model sessions are required for those checks. The portable helper has not been installed as the live watcher.

## Remaining limits

The current watch is session-bound and expires. It does not recover all missed history or report joins; a delayed response after a watcher lapse is documented in the current handoff. The scheduler state of every old session and third-party app was not exhaustively audited. Worker presence does not promise continuous availability. Workplace proxy, authentication and hosting changes remain unimplemented; the [handoff](workplace-handoff.md) describes what must be verified there.
