# Receiving Slack messages

The observed BetKalshi route is:

```text
Slack Web API → Python watcher → Claude Code Monitor → existing lead session
                                                      ↓
                                            CLI task + written brief
                                                      ↓
                                                Codex / Muse
                                                      ↓
                                     files + Slack post using worker token
```

Slack API polling and model polling have different costs. The Python watcher checks history every 20 seconds, prints only new relevant output, and makes no model calls. Monitor feeds that output into Claude. An empty check does not start a model turn. New-message events and Monitor expiry/renewal still consume attention; a busy channel is not free.

## Claude lead: the observed route

Use the existing watcher if it works. The live source and limits are recorded in [betkalshi-evidence.md](betkalshi-evidence.md). The portable [helper](../scripts/slack.py) has the same basic delivery behavior with environment-based configuration.

The setup agent supplies `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` through the existing local secret mechanism, and creates a private writable state directory. Keep one watcher and one state file for this lead/channel. Test identity with:

```sh
python3 scripts/slack.py auth
python3 scripts/slack.py history
```

Ask Claude to call its **Monitor tool**, rather than running a detached shell command and assuming stdout will reach Claude:

```json
{
  "command": "python3 -u scripts/slack.py watch --state /private-state/lead-seen.txt",
  "description": "new project Slack messages",
  "timeout_ms": 1800000
}
```

Run from the package directory, or use absolute paths. `/private-state/lead-seen.txt` is a placeholder; the setup agent supplies the actual writable path. The selected token is inherited by the Monitor command. `--token-env NAME`, placed before `watch`, selects another environment variable when preserving existing credential names.

On first run a new state file seeds the currently visible history without emitting it. Read history explicitly when taking over a channel. On every Monitor expiry notice, re-arm the watcher with the same state path. After a gap or a session restart, read missed history separately, including threads where relevant. Confirm a successor has an active watcher before retiring its predecessor.

[Anthropic's Monitor reference](https://code.claude.com/docs/en/tools-reference#monitor-tool), checked 28 October 2026, documents line-by-line delivery into the same session and a 30-minute maximum for an interactive watch. Tool availability can depend on the installed version and provider. Inspect the actual session. A shell process printing messages is not itself proof of model delivery.

### Inherited limitations

- Last 30 top-level posts; no pagination or complete outage recovery.
- For parents still in that window, reads up to 50 thread entries when the latest reply is within two hours. Older parents/replies can be missed.
- Suppresses the lead's own posts, `channel_join` and `bot_add`. Other workers' posts can reach the lead without a mention.
- Emits at most 600 characters of normalized text per message. Fetch full history/thread content for the task; files, blocks and attachments need their own reads.
- Deduplication is a local seen-timestamp file, not a durable model-delivery acknowledgment. Printing a line and recording it does not prove Claude acted on it. The state grows over time and concurrent use of one state file is unsupported.
- The portable watcher warns on unavailable thread reads while continuing top-level intake. Its read loop backs off for HTTP 429 `Retry-After`, including a rate limit during display-name lookup. Initial authentication and one-shot commands report failures and exit. Check actual Slack quotas and grants before copying the 20-second interval. It can be changed with `--interval`.

These bounds come from the working script. More reliable intake is possible, but is additional implementation work.

## Codex and Muse: direct tasks in the inspected setup

The lead launches an authenticated CLI with a brief and working directory. The observed command forms include `codex --search exec …` and `muse exec … --prompt-file …`. It reads their output/files and integrates the results. Workers receive enough project context and their brief; context does not automatically transfer across harnesses.

The inspection found actual task-specific runs. It did not establish an active independent mention receiver for either worker. A tagged Slack assignment is visible coordination; the separate CLI invocation is what starts these observed workers. Do not tell users a tag will wake an idle session unless you have verified a receiver for that session.

For a worker's authorized channel reply, the setup agent provides that worker's own token and channel through its environment. The helper reads text from stdin, so message text stays out of shell interpolation:

```sh
python3 scripts/slack.py --token-env SLACK_CODEX_BOT_TOKEN post < result-message.txt
```

It posts top-level and does not invoke a model. Follow the project's existing permission settings when launching workers. A posting identity and a model/session are separate things.

## Historical fallback and other transports

An older Claude lead session used a five-minute scheduled history check alongside Monitor. That check caught a join which the watcher excluded. The current inspected lead transcript shows repeated Monitor renewals; it does not establish that the old scheduled check is still active. A fallback can be retained when required by an actual gap, with its model-turn cost made explicit.

For a different harness, verify its receiving capability before choosing a scheduler, gateway or vendor integration. Socket Mode is another transport; it is not used by the inspected Python watcher. Adding it would be a separate change, with an app-level token and a receiver that actually forwards events into the intended session.
