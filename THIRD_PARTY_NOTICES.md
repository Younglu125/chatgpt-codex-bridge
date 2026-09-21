# Third-party source

CCB is an integration layer, not an original implementation of every underlying capability.
The directly vendored community repository is listed below. OpenAI's plugin format and official
plugin-creator helpers are platform/installation dependencies; their use does not imply endorsement.
Do not attribute the upstream Full backend's MCP, OAuth, pairing or tunnel implementation to CCB.

Full mode vendors [XiaoDuoYa/codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt)
at commit `9663b88753e35c76796c5bce000293e0bd22cd9e` (upstream package 0.1.3).
Source and its MIT license are retained under `vendor/codex-with-chatgpt`.
The upstream skill is retained as the Full-mode runbook but is not separately activated. Our own
skill selects the mode and coordinates the analysis-to-implementation handoff.

All 70 tracked files are byte-identical to the pinned upstream commit; there are no vendored
runtime or test edits. The adapter isolates state under BRIDGE_STATE_DIR/full and fixes the
workspace to the registered checkout while exposing the complete upstream command surface.
Updating the vendored revision is an explicit maintenance operation followed by tests.

Native/snapshot bridge code and integration workflow: ChatGPT Codex Bridge contributors.
No affiliation with or endorsement by OpenAI or the upstream authors is implied.
