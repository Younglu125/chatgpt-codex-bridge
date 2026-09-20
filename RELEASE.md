# Release acceptance

0.2.7 is a portable integration release candidate until a second machine validates installation.
The target ChatGPT connector path has been exercised. Do not turn this label into a verified-stable
claim by editing docs.

1. Run Python tests, vendored backend build/tests and plugin/skill validators.
2. Generate an allowlisted package using package_plugin.py. Scan output for personal home paths,
   account/chat/tunnel IDs, secrets, validation transcripts and unexpected symlinks.
3. Extract the ZIP to a new directory with spaces. Run Lite setup/doctor/auto-project and a fixture job
   with an empty state directory. No reference to the author's source tree may be needed.
4. In the installed package run Full setup (locked dependencies). Test loopback MCP/OAuth and
   path boundaries; then configure the user's own ChatGPT connector and verify workspace_info/read_file.
5. Run a real analysis → implementation/test → independent review with that user's own ordinary chat.
   Record source of model label. Browser and native routes need separate acceptance.
6. Publish only after reviewing output and license notices. No automatic GitHub push, X post or public
   plugin-directory submission is performed by packaging. Keep personal state and audit reports local.

Scope for the first supported release: macOS with Python 3.12+, Codex local execution and ordinary
ChatGPT access. Linux/WSL2 are candidates until tested; native Windows is not advertised. Include exact
client/runtime versions in bug reports. Git-backed marketplace availability depends on Codex surface.

An upstream upgrade is explicit: select a commit, review its diff/license, regenerate the lockfile and
manifest, run tests, then make a new version. Never replace a running user's backend with latest blindly.
