# Handoff to a cloud services team

This package documents an observed local workflow. It has not been integrated with an employer's API proxy, identity provider or cloud platform. The starting point is one listening lead and workers invoked for tasks; [the dated evidence](betkalshi-evidence.md) states the proof and limits.

## Dependencies actually used

| Path | Current implementation | Workplace question |
| --- | --- | --- |
| Slack reads | Python standard-library HTTPS calls to `https://slack.com/api/`, authenticated with a bot token | Which workspace installation, grants, outbound route and credential store will be approved? |
| Lead delivery | Python stdout enters the existing Claude Code session through Monitor | Does the selected provider/build expose Monitor, and who owns renewal/recovery? |
| Lead model access | Existing interactive Claude login in the inspected setup | What is the approved employer authentication/model route? |
| Worker execution | Existing Codex/Muse CLIs, task briefs, directories and model settings | Which installed harnesses can use the approved model proxy with their required tools? |
| Worker replies | `chat.postMessage` with each worker's bot credential | How are those credentials made available to the intended process? |
| Files/state | Local project work areas, briefs/results and seen-timestamp file | Where will work run, and how are those files retained or recovered? |

Model access and Slack access are separate network paths. Routing model requests through an API proxy does not itself deliver Slack messages, provide CLI tools, or make an idle worker listen.

## Reproduce the known path first

The setup agent inventories the target workplace environment and fills the table with actual endpoint/authentication choices. Reuse an existing project/channel/lead where available. Check each chosen CLI's installed help and the organization's provider documentation: this repository does not specify invented universal proxy variables or a gateway schema.

For the included Python helper, normal Python HTTPS proxy behavior applies through `urllib.request`. Custom Slack API origins, proxy-specific credentials, managed certificate installation and the employer's TLS/network rules have not been implemented or tested by this package. Determine whether Slack access is direct, through a standard forward proxy, or through a different internal API before adapting code. Secrets belong in the approved workplace store and process environment.

The inspected local setup uses existing subscriptions/logins. That observation is not a deployment recommendation or proof those same accounts may be used at work. Choose the approved provider route before claiming the worker can operate there. Preserve the intended tools and autonomy; permission changes are an explicit workplace configuration choice.

## Demonstrate the handoff

Use a target-channel test within the authorized setup scope:

1. An ordinary untagged human message reaches the intended lead session; retain its message timestamp and the runtime receipt.
2. The lead starts one bounded task through a selected worker's actual execution route. Verify its working directory, required tools and result.
3. The result returns under the expected Slack identity and the lead can respond to it.
4. Renew the Monitor once and verify receipt afterward. Stop/restart the session and demonstrate the documented history catch-up procedure. Identify the gaps that procedure cannot recover.

Those are checks of the selected route, not requirements to implement a generic agent platform. Record the owner of the processes and how to stop them. The optional [team note](../assets/TEAM_CONTEXT.template.md) can hold the small operational record.

## Reliability decisions still open

The 30-minute Monitor lifetime and limited history window are material limitations. Retain a fallback only when the intended service level needs it, with its model-call cost stated. A longer-lived push receiver, complete history reconciliation or unattended cloud orchestration would be additional work. Pick that scope with the team after reproducing the current route; none is included or claimed here.

Official references: [Monitor](https://code.claude.com/docs/en/tools-reference#monitor-tool), [Python HTTPS/proxy handling](https://docs.python.org/3/library/urllib.request.html), [Slack history](https://docs.slack.dev/reference/methods/conversations.history/), [posting](https://docs.slack.dev/reference/methods/chat.postMessage/). Provider support and workplace policy require fresh verification in the target environment.
