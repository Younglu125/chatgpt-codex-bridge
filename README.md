# ChatGPT Codex Bridge · CCB

**Keep coding with Codex. Bring ordinary ChatGPT in when another perspective is worth the handoff.**

English | [简体中文](README.zh-CN.md)

[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![Preview](https://img.shields.io/badge/status-preview-orange.svg)](VALIDATION.md)

CCB is an independent Codex plugin. Ordinary ChatGPT helps with substantial planning, major
decisions and independent review. Codex owns local edits and tests.
No ChatGPT Work, private account APIs or OpenAI API key required.

## Background: why build this?

Codex is useful for reading code, editing files and running tests. For substantial planning or an
independent review, you may also want the ordinary ChatGPT conversation you already use to help.
Manually copying context, tracking replies and carrying conclusions back interrupts that workflow.

CCB organizes this handoff instead of replacing Codex or calling another model for every step:
enable collaboration for a conversation, provide bounded evidence when useful, then let Codex
continue local execution. Reducing some Codex analysis work is a motivation, not a measured quota
saving or speed guarantee. ChatGPT analysis can itself involve a substantial wait.

This is an integration and extension of existing community and platform capabilities, not an
all-from-scratch implementation of the underlying technology.

## Upstream integration and acknowledgements

Thanks to [XiaoDuoYa/codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt), the direct
upstream of CCB Full. CCB vendors a pinned revision and reuses its read-only workspace MCP,
OAuth/pairing, tunnels and execution evidence. Users do not need to clone that repository separately.

| Source | How CCB uses it | Attribution boundary |
|---|---|---|
| `codex-with-chatgpt` (MIT) | Vendored pinned source; revision and hashes in [UPSTREAM.json](UPSTREAM.json) | The Full backend is upstream work, not CCB-original functionality |
| OpenAI Codex plugin specification and official plugin-creator helpers | Plugin packaging and convenience installation; [official guidance](https://developers.openai.com/plugins/build/plugins) | Host capabilities and installation dependencies, not a CCB-built chat service |
| CCB integration layer | Selective conversation participation, Lite snapshots, project/chat binding, handoff records and recovery, packaging and privacy checks | Workflow and tooling added around the above capabilities |

The upstream source, MIT license and attribution are retained.
Other dependencies retain their own manifests and licenses. See [third-party notices](THIRD_PARTY_NOTICES.md).
No endorsement by upstream authors or OpenAI is implied.

## A small switch, a natural workflow

| Your request | What happens |
|---|---|
| Fix this small bug | Codex directly |
| CCB, help plan this refactor | Enable collaboration; consult ChatGPT |
| Implement the agreed approach | Codex edits and tests |
| Reconsider the architecture | Consider another ChatGPT analysis |
| Handle this step yourself | Codex this time; collaboration stays on |
| Ask GPT for help on this step | Explicit one-off consultation |
| Exit CCB | Return to Codex-only |

Intentional requests using `CCB`, `ccb`, `$CCB` or `$ccb` enable the current conversation.
Follow-ups inherit the preference; new conversations default to Codex.
Phase words are optional. Quotes, code, negation and plugin maintenance do not activate collaboration.

This is **skill-driven**, not a global message interceptor. Codex interprets intent and calls the
session helper. The shorthand does not register a separate skill named CCB; if your client
cannot resolve it, invoke `$chatgpt-codex-bridge`.

## Why CCB?

- Selective handoffs: routine edits, status checks, tests and small fixes stay with Codex.
- Lite snapshots or live, read-only workspace access.
- Per-project jobs and saved replies for recovery without duplicate sends.
- Separate conversation preference, workspace identity and ChatGPT target.
- Full readiness requires ChatGPT to read the correct workspace and a real file.
- Distributable packages exclude personal runtime state.

**Net token savings, billing attribution and speed improvements have not been measured.**
Handoffs add latency. Use ChatGPT where its expected contribution outweighs that cost.

## Lite and Full

| Route | Evidence available to ChatGPT | Requirements |
|---|---|---|
| Lite / prompt | Question only | Python 3.12+, Codex, ordinary ChatGPT, working native or browser messaging |
| Lite / snapshot | Selected filtered frozen files | Lite plus permission to share those files |
| Full / live | ChatGPT itself reads current files, searches, and inspects Git diffs and recorded execution output through MCP on demand | Lite plus Node.js 20+/npm, cloudflared, custom MCP/OAuth access |

**With Lite snapshots, Codex selects files and sends frozen contents. With Full, ChatGPT decides what
to inspect and uses an authorized local read-only MCP service to list directories, search and read
current project files. Codex does not need to package the files in advance.**
Full is limited to permitted contents within the authorized workspace, not arbitrary files on your computer.
Codex still performs authorized edits and test runs; ChatGPT can inspect recorded execution results through MCP.

Optional frozen-snapshot MCP requires the Python MCP extra and separate HTTPS/OAuth setup.
Full uses the pinned [codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt) backend.
CCB adds packaging, job/evidence handoff and selective conversation coordination.
Upstream source and licenses are preserved; see [attribution](THIRD_PARTY_NOTICES.md).

Native tools or the browser deliver messages; MCP exposes files. Native chat success alone does not
prove Full access. Healthy project connections are reused.

## Install

**0.2.9 preview.** macOS has been exercised. Linux/WSL2 remains a compatibility target.
Native Windows is not supported by CCB's POSIX snapshot/locking layer.

### 1. Get the program

Clone with Git or extract a release ZIP into a permanent directory.

- **Git clone:** convenient for future updates. If repository access is restricted, obtain access first.
- **Release ZIP:** read the root `INSTALL.md` after extraction; plugin source is under
  `plugins/chatgpt-codex-bridge/`. GitHub's source ZIP has a different layout: its installation scripts
  are directly under the extracted repository root.

The release includes Lite/Full source and the pinned upstream code, but is not an offline installer.
Accounts, authorizations and preinstalled dependencies are not included. **A complete package is not
an already-connected Full setup.** Use your own account to configure and verify your local setup.

First clone (if the destination exists, inspect it; do not overwrite or initialize it again):

```bash
git clone https://github.com/Younglu125/chatgpt-codex-bridge.git
cd chatgpt-codex-bridge
```

### 2. Install the plugin

Run the following commands from the plugin source root. For a release ZIP, first enter
`plugins/chatgpt-codex-bridge/`, not the outer extracted directory.

```bash
python3 --version                         # 3.12+
python3 scripts/install_plugin.py         # First install: Lite; updates preserve Full
python3 scripts/install_plugin.py --mode full  # If you want Full
```

The convenience installer requires Codex CLI on PATH and the official plugin-creator helpers.
Otherwise use the release ZIP's marketplace:
`codex plugin marketplace add <extracted-directory>`, then install CCB from that marketplace.
See [official packaging guidance](https://developers.openai.com/plugins/build/plugins).

### 3. Start using CCB and complete first-time setup

**Open a new Codex task after installation/update.** In your actual project ask:

> CCB, analyze this project and recommend the next step.

For Full, the skill identifies the checkout, sets up its project-bound backend, and guides connector
creation/OAuth. You handle login, CAPTCHA/2FA and necessary consent.
Each project/Mac needs correct local setup and real workspace/file-read verification.
Temporary tunnel addresses may change after restart; a fixed domain is optional.
Never copy credentials or runtime state from another machine.

Verify an actual request and complete reply first. For Full, additionally verify that the connector
reads the correct workspace and file. Installation, a running service or a connector name is not
that proof.

### 4. Update

Routine Git updates: `git status`, `git pull --ff-only`, reinstall, then open a new task.
Preserve and resolve local changes/divergence first. Maintainers with pre-cleanup history must follow
the [one-time migration note](OTHER_MAC_UPDATE.zh-CN.md), not merge the old history back.

## Recovery

```bash
python3 scripts/doctor.py
python3 bridge.py auto-project --root .
python3 bridge.py pending --project PROJECT
python3 scripts/route.py --project PROJECT --scope repository
python3 scripts/session.py --thread CODEX_CONVERSATION_ID
python3 scripts/full.py --project PROJECT -- status --json
```

Full is read-only. Codex still needs authorization for implementation.
Analysis-only requests stop at analysis. Review substantial milestones, not every edit/test cycle.
An explicit GPT request overrides the normal cost/latency choice.

## Privacy

State lives outside the plugin at `~/.local/share/chatgpt-codex-bridge` or `BRIDGE_STATE_DIR`.
Never share that directory, transcripts, credentials, pairing codes or personal chat URLs.

Lite snapshots send file contents selected by Codex to ChatGPT. With Full, ChatGPT initiates MCP read
requests and the local service returns permitted contents to ChatGPT; Codex does not package and upload
those files in advance.
**Read-only does not mean data stays on your Mac.** Filtering is not a secrecy guarantee.
Review scope before allowing a handoff.

```bash
python3 scripts/audit_share.py . --tracked --history
python3 scripts/release.py --output release
```

The heuristic scanner reports common private patterns without printing their values.
Inspect images visually and Git metadata separately. A clean ZIP does not sanitize Git history.
See [sharing review](SHARING_REVIEW.md), [release checklist](RELEASE.md) and [validation](VALIDATION.md).

## Screenshots and contributing

[Demonstration screenshots and X drafts](marketing/README.md) use actual local helper output.
They are CLI demonstrations, not fabricated ChatGPT conversations or fresh Full proofs.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest==9.1.1 mcp==1.30.0
.venv/bin/python -m pytest -q
```

Test before committing. Keep the upstream pinned; upgrades are explicit.
On another Mac, preserve changes, pull fast-forward, reinstall and open a new task.

[Chinese operation guide](USAGE.zh-CN.md) · [Workflow](WORKFLOW.md)

MIT © contributors. Independent community project; not an official OpenAI product.
