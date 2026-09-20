# ChatGPT Codex Bridge

Ordinary ChatGPT analyzes and reviews; Codex implements and tests in your current local project.
New conversations use Codex directly. An intentional `CCB`, `ccb`, `$CCB`, or `$ccb` request enables
conversation-scoped collaboration until disabled. Follow-ups inherit it without another marker.
Codex selectively consults ChatGPT for substantial analysis, major decisions and independent review;
routine edits, tests and small fixes stay local. Explicit GPT requests override that cost/latency choice.
Phase words are optional. Mentions, quotations and negation do not activate collaboration.
`scripts/session.py` persists the preference by Codex conversation ID; the skill interprets intent
and invokes it (there is no automatic host hook). New conversations remain independent.
Version 0.2.8 combines native conversation messaging and frozen evidence with the unmodified,
pinned live workspace MCP implementation from [codex-with-chatgpt](https://github.com/XiaoDuoYa/codex-with-chatgpt).
No OpenAI API calls or API keys are required by these routes. The plugin does not increase
subscription limits; actual quota savings have not been measured.

中文安装与使用：[USAGE.zh-CN.md](USAGE.zh-CN.md)

## Automatic route: reuse first

The user does not choose a transport for every task. The bridge identifies the current checkout and
checks that project's saved state. If its authorized Full connection is running, it is reused. A
repository-wide question uses Full because ChatGPT must discover and traverse files. A small question
with already-known files automatically falls back to a frozen snapshot when Full is unavailable. A
question needing no local files sends only the prompt.

`scripts/route.py --project PROJECT --scope prompt|bounded|repository` makes this decision. It does
not mistake a local process, tunnel or issued token for a working ChatGPT connection: live reuse
requires a saved ChatGPT chat that passed workspace identity and file-read verification.

## Modes and evidence

| Mode | Local evidence | Necessary conditions | What is optional |
|---|---|---|---|
| Lite / prompt | None | Python 3.12+, macOS/Linux/WSL2, Codex with local execution, ordinary ChatGPT chat, native tools OR browser access | Node, MCP, tunnel, API key, developer mode are unnecessary |
| Lite / snapshot | Explicit filtered frozen files in a message | Same as Lite; permission to send those project contents | Same optional dependencies |
| Frozen MCP | Approved immutable job snapshot, six read-only tools | Python MCP extra, remote HTTPS/OAuth connection available to ChatGPT | Live workspace backend unnecessary |
| Full / live | Current files, search, Git diff, actual execution records; nine read-only tools | Lite requirements + Node >=20/npm + custom MCP available in ChatGPT + configured OAuth HTTPS connection | cloudflared is needed for bundled tunnels; fixed domain optional |

Full's messages may use native tools OR the browser. MCP provides data, not message delivery.
Native kind=chatgpt alone does not prove ordinary Chat, selected model or billing attribution.
No route silently switches to ChatGPT Work or a paid model API.

## Install from a release

1. Extract the release into a permanent directory (any path, including spaces).
2. `python3 scripts/setup.py --mode lite` checks local prerequisites, with no network dependency install.
3. Register the package with your Codex plugin system. For local personal installation, run
   `python3 scripts/install_plugin.py` for Lite or `python3 scripts/install_plugin.py --mode full`
   when Full is wanted on this machine. Later runs of the default `auto` mode preserve a previously
   built Full installation. It copies a self-contained generated package and registers
   the default personal marketplace through Codex's official plugin-creator helper, when that helper
   is installed. If unavailable, follow the official plugin installation documentation linked below.
4. Start a new Codex task to load the installed version. Ask Codex to bind an existing ordinary
   ChatGPT chat once. Use a dedicated chat per project if history separation matters. A global
   legacy target remains usable; no author's account or target is shipped.
5. In your actual project ask:

> CCB 在本项目下处理【问题】。

The current checkout/worktree determines the project; you need not repeat its path.
If the task is in an ambiguous umbrella directory, identify which project once.

For Full use `python3 scripts/setup.py --mode full`, register the current checkout, then follow the
vendored upstream setup unchanged: run `scripts/full.py --project PROJECT -- sandbox-allow --json`
and `scripts/full.py --project PROJECT -- setup --json`. Upstream setup creates its read-only MCP,
OAuth pairing and default Cloudflare Quick Tunnel; no domain, Cloudflare account or OpenAI API key is
needed. `sandbox-allow` performs the same Codex settings change documented by upstream. ChatGPT
login/2FA, connector creation and consent remain account-owner actions. A fixed domain stays optional.
After that one-time authorization, the project connection is reused; ordinary tasks must not repeat setup.

## Lifecycle and recovery

- `python3 scripts/doctor.py`: read-only local readiness; native/browser/remote MCP remain unknown until exercised.
- `python3 bridge.py auto-project --root .`: reuse/register this checkout, including worktrees.
- `python3 scripts/route.py --project PROJECT --scope repository`: choose live reuse or the necessary fallback.
- `python3 bridge.py target CHAT_ID --project PROJECT --model 'visible model' --proof 'ordinary Chat verified in UI'`; omit `--model` when native tools do not expose it. The stored value remains null rather than guessed.
- `python3 bridge.py pending --project PROJECT`: project-scoped checkpoints. A timeout does not resend a request.
- `python3 bridge.py check JOB`: frozen evidence drift; live mode requires actual Git/file recheck.
- `python3 bridge.py complete JOB --input REPORT.md`: close an analysis-only job without claiming implementation.
- `python3 scripts/full.py --project PROJECT -- status --json`: Full backend and authorization status.
- `python3 scripts/full.py --project PROJECT -- unpair`, then `stop`: revoke and stop Full.
- `python3 bridge.py revoke JOB`: revoke only a frozen snapshot's MCP access.

Upgrade by reviewing a versioned release, running its tests, reinstalling the package and opening
an updated task. Dependencies/upstream do not update silently. The installer builds Full dependencies
before registering the new plugin when Full is selected or was already installed. Existing external
project state and authorization are reused. Reinstall the previous release to roll back;
0.2 preserves the v1 state schema and old jobs. Before upgrades, back up that state locally.
Uninstall via Codex's plugin manager after stopping/revoking Full projects. Uninstalling the plugin
does not delete history or revoke a still-running remote connection; keep or manually archive state.

## Data and boundaries

Personal targets, project paths, transcripts and credentials are stored outside the release under
`~/.local/share/chatgpt-codex-bridge`; override with BRIDGE_STATE_DIR. Full state is isolated beneath
that directory in `full/`. Never publish this directory. Snapshot filtering excludes hidden files,
credentials, databases and common generated folders, rejects symlink traversal, and redacts common
secret patterns. Review export scope; filtering cannot guarantee removal of every possible secret.
Full exposes a read-only workspace and uses its upstream ignore/OAuth policies; see the vendored
security documentation. All tracked upstream files remain byte-identical to the pinned GitHub commit;
the outer adapter only supplies the registered workspace and isolated state directory. Both routes
send selected project content to the user's ChatGPT account.

Snapshot MCP remains available via `python3 scripts/setup.py --mode snapshot-mcp` and `.venv/bin/python server.py`.
For remote snapshot MCP the legacy `scripts/public-mcp` manages an OAuth Quick Tunnel; its URL is temporary.
It is deliberately not auto-started for Lite. Official Secure MCP Tunnel is an advanced optional alternative,
not part of required installation. Full uses its separate live backend and pairing flow.

## Sharing and release

`python3 scripts/package_plugin.py --output /path/to/chatgpt-codex-bridge` builds from an explicit
allowlist; no local state, validation transcripts, venv, node_modules or private target IDs are included.
`python3 scripts/release.py --output /path/to/release-directory` produces a versioned ZIP, SHA256 and
Git-backed marketplace layout. See [RELEASE.md](RELEASE.md) for clean-install acceptance.
Do not promise universal platform support or fixed token savings merely because local tests pass.
The delivered VALIDATION.md states observed and unverified coverage.

License: MIT; upstream attribution and preserved license: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
The upstream skill is kept as the Full-mode runbook but is not separately activated, avoiding two
competing skill triggers. This outer skill only selects a mode and coordinates ChatGPT with Codex.
This is an independent community project.

Official packaging and marketplace guidance: https://developers.openai.com/plugins/build/plugins
