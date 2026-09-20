# Validation — 0.2.9 integration candidate

0.2.9: 61 Python tests and 172 pinned-backend tests (17 files) passed on macOS ARM64.
The release ZIP privacy gate passed; two rendered local routing screenshots were visually reviewed.
This release adds privacy-scanner regression tests and local routing demonstration screenshots.
These screenshots do not send GPT messages or establish new Full connector acceptance.
See SHARING_REVIEW.md for the separate Git-history privacy limitation.

2026-09-20 update: 56 Python tests passed, including CLI subprocess tests for
conversation persistence, isolation, temporary local override, mandatory one-off GPT assistance,
explicit exit and path-safe state storage. Pinned upstream: 172 tests in 17 files passed;
Full installation and TypeScript build passed. The upstream source remains unchanged.
Session routing is deterministic once Codex supplies intent/phase. Natural-language interpretation
and skill activation remain agent responsibilities; these tests do not claim automatic host hooks,
universal trigger recognition, quota savings or a new remote MCP acceptance run.

The following is historical 0.2.7 acceptance evidence; its test counts and runtime versions
describe that earlier run, not the 0.2.8 run above.

Observed on 2026-09-19, macOS ARM64. This is a locally tested release candidate,
not a claim of universal or remote-connector stability.

| Check | Result |
|---|---|
| Python bridge tests | 52 passed, including an honest terminal state for analysis-only work, Full routing that rejects a saved chat from another account target, project-scoped pending recovery, native recovery of old marker-only cancellations, account-switch target rebinding without invented model metadata, snapshot/OAuth/HTTP tests, portability, project isolation, browser capture rejection, review limits, complete Full command passthrough and vendored hash checks |
| Pinned upstream build | TypeScript build passed on Node 22.19.0 |
| Pinned upstream parity | Live comparison against GitHub `main` commit `9663b88753e35c76796c5bce000293e0bd22cd9e`: all 70 tracked files present and byte-identical; no local adaptations |
| Pinned upstream tests | 178 passed in 17 files, including live MCP, OAuth, workspace paths, execution output and session state |
| Skill and compatibility plugin validators | Passed |
| Actual Codex loader | New bridge skill enabled, no loader errors; Lite intentionally registers no always-on MCP |
| Clean package | Copied into an unrelated directory with spaces, empty state, Python -S (no third-party packages); Lite setup/doctor/auto-project passed |
| Installed Full dependencies | npm ci and build passed inside installed plugin cache, separately from source checkout |
| Full adapter live service | Started for the exact registered fixture root, returned matching workspace ID, unauthenticated MCP returned 401, execution record/output saved, service stopped after test |
| Complete upstream setup passthrough | The project-bound wrapper ran upstream `sandbox-allow` and `setup` unchanged; setup returned the expected connector/workspace/tunnel fields, started a real Cloudflare Quick Tunnel for the fixture workspace, then access was revoked and the service stopped |
| Actual native ChatGPT roundtrip | Existing kind=chatgpt target received exact snapshot prompt; complete matching response was collected, implementation made, eight unittest cases passed |
| Real-state route regression | A registered project had a live process and Quick Tunnel but zero issued authorization tokens; repository scope correctly selected one-time Full setup while bounded scope automatically selected snapshot with no user action |
| Actual independent review | A linked child snapshot with source, tests and actual output was sent to the same ordinary chat; complete reply returned PASS with file/line evidence |
| Browser capture adapter | Automated input validation passed; actual ordinary ChatGPT browser messaging was exercised during Full MCP verification |
| ChatGPT remote Full MCP | VERIFIED in an ordinary ChatGPT chat whose UI showed model `6 Pro`: OAuth auto-discovery, DCR, PKCE S256, pairing and token exchange completed; ChatGPT called `workspace_info` and `read_file`, returning the matching fixture identity and actual source content |
| Unpredictable live-read proof | After the connector was authenticated, Codex created a new file containing a random value that had never appeared in the chat. ChatGPT immediately returned that exact value through `read_file`, proving the result came from the live workspace rather than prior conversation context |
| Linux/WSL2 | CI workflow supplied, not executed on those platforms in this task |
| Native Windows | Not supported by the POSIX snapshot/lock implementation |
| Quota attribution/savings | Not measured. The Full browser test directly observed the UI label `6 Pro`; native thread tools still do not return the selected model |

Private native request/response records remain only in the local runtime job store and are excluded
from the distributable. Source includes no personal chat IDs or absolute installation paths.
The Full test also confirmed nine read-only tools in ChatGPT. Connector creation, OAuth discovery,
pairing and the live file-read proof used the original upstream implementation without source changes.

Before promoting this candidate to a stable public release, finish a clean installation on another
user's machine. If UI/API capabilities differ, report the
unsupported combination rather than claiming fallback is universal.
