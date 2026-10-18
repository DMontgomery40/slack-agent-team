# pstack for personal assistants (optional)

**Recommended, not required.** Offer @poteto's pstack to personal-assistant agents as a shared skill set, in any harness. If the user accepts, or already uses it, set it up. If they decline, note that and carry on. Setup never waits on pstack.

## Source

[Lauren Tan (@poteto)'s official pstack](https://github.com/cursor/plugins/tree/main/pstack). The reviewed revision is `019a6a20592c10bf92869e5740368f578a9997fd` (plugin version `0.15.25`, October 17, 2026); see the [dependency record](../assets/pstack-source.json). It's MIT licensed and isn't copied into this repository. Don't mistake an unofficial fork for the canonical source.

## Install

- **Cursor:** `/add-plugin pstack`.
- **Claude Code:** `/plugin marketplace add cursor/plugins`, then `/plugin install pstack@cursor-plugins`. See the [Claude adapter](https://github.com/cursor/plugins/blob/019a6a20592c10bf92869e5740368f578a9997fd/pstack/docs/harness/claude-code.md).
- **Other harnesses** (Codex, Muse, Hermes, OpenClaw, dots, Grok): use the harness's own skill or file mechanism, or a source checkout. If an assistant can't open files, give it the full text of the skills it needs. A link it can't read doesn't count.

Run these yourself through the harness. Don't hand the commands to the user. Marketplace installs can be newer than the reviewed revision, so check the installed version.

## Use

- **Substantive personal work:** route it through `poteto-mode`.
- **Small daily tasks:** use the relevant skill directly, for example `sharpen`, `unslop`, `ketchup`, `recall` or `show-me-your-work`.
- **Engineering playbooks** apply only when the task is engineering.
- **Personal knowledge** shared across assistants goes in the private `SHARED_MEMORY.md`. pstack supplies methods, not memory sync.
