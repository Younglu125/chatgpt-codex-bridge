# Full: live project MCP and independent review

The complete upstream backend and runbook are pinned in vendor/codex-with-chatgpt; see
THIRD_PARTY_NOTICES.md. Its tracked files remain byte-identical to the pinned GitHub commit.
This outer skill only selects Full for the current project and coordinates the returned plan with
Codex implementation. Native messaging and browser messaging both work with this data backend.
Full itself requires no OpenAI Platform API key.

## Default setup: Quick Tunnel, no domain

1. `python3 <plugin-root>/scripts/setup.py --mode full` uses npm ci with the upstream lock and builds the backend. Requires Python 3.12+, Node >=20 and npm. Install cloudflared through the user's normal package manager. No public server starts during dependency installation.
2. Register the actual checkout with bridge auto-project. All backend calls use:
   `python3 <plugin-root>/scripts/full.py --project PROJECT -- COMMAND ...`
   The adapter only injects the registered `--workspace` and isolates `C2C_STATE_DIR` under bridge state/full. Never pass another `-w/--workspace`. It exposes the complete upstream command surface, including setup, doctor, repair-related restart, prefs, session, record, tunnel and update-check.
3. Follow upstream first-time setup in `vendor/codex-with-chatgpt/skill/SKILL.md`: run `sandbox-allow --json`, then `setup --json`. `sandbox-allow` makes the documented Codex settings change; `setup` starts the read-only bridge, creates the upstream default Quick Tunnel and returns the connector identity and pairing data. Do not replace these with another MCP/OAuth implementation.
4. Follow the upstream automatic or guided-manual ChatGPT connector flow exactly for that workspace's connector. The user handles login, CAPTCHA/2FA and consent. Never extract cookies or tokens. If custom MCP/developer mode is unavailable under the account policy, Full remains unavailable; keep Lite usable.
5. Verify from the same ordinary ChatGPT chat exactly as upstream requires: call `workspace_info` and `read_file` on a harmless approved file. Confirm returned workspace identity and actual content match local `workspace --json`. A green local doctor or connector icon is insufficient.

Quick Tunnel is the upstream default and provides the complete feature set without a domain or Cloudflare account. Its URL may change after restart; use the upstream doctor/reconnect flow for that project's connector and repeat the identity/read check. A named Cloudflare tunnel is an advanced upstream option for users who explicitly want a stable hostname.

After first verification, reuse is the default. `scripts/route.py` requires the project service,
tunnel, an issued authorization token and a saved ChatGPT chat that passed workspace/file verification
before selecting live mode. The saved chat ID must match the current account target; after an account
switch, re-verify and save the current chat without repeating OAuth when that account's connector is
already authorized. Run `doctor` to repair
an existing connection; do not repeat setup, create another connector, or ask the user to repeat
authorization unless the current account no longer has this project's connector or authorization.

## Plan → execute → review

- `prepare PROJECT --transport live --goal '...'` makes a short control prompt without embedding local file contents. Send/collect with the same native or browser adapter as Lite. ChatGPT can call the backend's nine read-only tools: workspace_info, list_directory, read_file, search_workspace, git_status, git_diff, test_status, execution_summary, execution_output.
- Before sending ensure the correct connector is usable in that chat. ChatGPT should independently inspect needed files, identify missing evidence and return a concrete plan. The live workspace can change: record Git identity and reconcile scope before implementation.
- Codex implements in the root saved in the job. Capture real test/build stdout/stderr in a local file. Record success AND failure:
  `record --task JOB --iteration 1 --changed-files 'src/file.py' --tests 'actual summary' --exit-status ok --command 'actual command' --output-file LOG --exit-code 0`
  Match exit-status/code to reality. The backend filters output before exposing it; restricted output is not proof that a test passed. Do not send arbitrary shell history or secrets.
- Save a truthful local report and `bridge finish JOB --input REPORT`. Prepare a child review job with `--parent JOB --transport live`, include the parent task ID in its goal and ask ChatGPT to inspect git_diff and actual execution_output for THAT task/iteration. Include user goal/success criteria so review does not guess. Send/collect independently. Review response must say PASS, FIX or BLOCKED and cite evidence; a completion marker alone does not mean PASS.
- If FIX, apply justified fixes, run tests again, record under that review job's ID, finish and request another child review. Maximum three review rounds; summarize remaining issues at the limit. PASS requires actual relevant checks; never label unobserved tests verified.
- Run `bridge pending` to resume: prepared → send once; dispatching/sent → inspect existing request and collect; analyzed → implement remaining work. implemented → local work finished; a linked review is separate. Never re-execute just because browser waiting timed out.
- `unpair` revokes this project's access; `stop` stops this project's service. bridge revoke only revokes the FROZEN Python MCP job, not Full's workspace token. Explain this distinction when disconnecting.

## Platform boundary

Integration supported baseline: macOS; Linux/WSL2 are intended compatible targets and must pass CI before being advertised as verified. Native Windows is not supported by our POSIX snapshot/locking layer, even though the upstream backend supports it. Browser and native tools vary by Codex surface; declare unsupported combinations explicitly.
