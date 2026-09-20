# ChatGPT Codex Bridge · CCB

**Keep coding with Codex. Bring ordinary ChatGPT in when another perspective is worth the handoff.**

English | [简体中文](README.zh-CN.md)

[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![Preview](https://img.shields.io/badge/status-preview-orange.svg)](VALIDATION.md)

CCB is an independent Codex plugin. Ordinary ChatGPT helps with substantial planning, major
decisions and independent review. Codex owns local edits and tests.
No ChatGPT Work, private account APIs or OpenAI API key required.

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
| Full / live | File reads, search, Git diffs, recorded execution output | Lite plus Node.js 20+/npm, cloudflared, custom MCP/OAuth access |

Optional frozen-snapshot MCP requires the Python MCP extra and separate HTTPS/OAuth setup.
Full uses the pinned [codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt) backend.
CCB adds packaging, job/evidence handoff and selective conversation coordination.
Upstream source and licenses are preserved; see [attribution](THIRD_PARTY_NOTICES.md).

Native tools or the browser deliver messages; MCP exposes files. Native chat success alone does not
prove Full access. Healthy project connections are reused.

## Install

**0.2.9 preview.** macOS has been exercised. Linux/WSL2 remains a compatibility target.
Native Windows is not supported by CCB's POSIX snapshot/locking layer.

Clone this repository (access required), or extract a release into a permanent directory.
Check existing changes before updating, use `git pull --ff-only`, and resolve divergence normally.

```bash
python3 --version                         # 3.12+
python3 scripts/install_plugin.py         # First install: Lite; updates preserve Full
python3 scripts/install_plugin.py --mode full  # If you want Full
```

The convenience installer requires Codex CLI on PATH and the official plugin-creator helpers.
Otherwise use the release ZIP's marketplace:
`codex plugin marketplace add <extracted-directory>`, then install CCB from that marketplace.
See [official packaging guidance](https://developers.openai.com/plugins/build/plugins).

**Open a new Codex task after installation/update.** In your actual project ask:

> CCB, analyze this project and recommend the next step.

For Full, the skill identifies the checkout, sets up its project-bound backend, and guides connector
creation/OAuth. You handle login, CAPTCHA/2FA and necessary consent.
Each project/Mac needs correct local setup and real workspace/file-read verification.
Temporary tunnel addresses may change after restart; a fixed domain is optional.
Never copy credentials or runtime state from another machine.

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

Lite sends selected contents to ChatGPT. Full sends contents actually requested through MCP.
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
