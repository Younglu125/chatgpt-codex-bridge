# Sharing review · 0.2.9

## Findings and changes

- Removed a developer-specific umbrella-folder name from project registration. Root/home guards remain;
  callers still select a single project through the skill's workspace rules.
- Added equivalent English and Simplified Chinese landing pages, installation prerequisites,
  selective collaboration examples, fallback guidance, privacy boundaries and upstream attribution.
- Added a source/package privacy scanner and a release-time gate. Reviewed synthetic fixtures are
  exempt only while their exact SHA256 remains unchanged; modified fixtures require a new review.
- Clarified that shorthand activation is interpreted by the skill, not a registered host command.
- Screenshots use isolated fictional session IDs and actual local CLI outputs; they do not show
  private accounts, personal paths, credentials, chat history or live tunnel URLs.

## Remaining release boundaries

Historical status on 2026-09-20: the repository was private; a shareable README alone did not grant anonymous clone access.
The owner made the repository public on 2026-09-21. This does not change the historical privacy limitations below.
On 2026-09-20, the owner authorized rewriting an earlier commit's private author/committer identity
to the maintainer's GitHub noreply identity. The rewritten history preserves every commit's file tree.
Both main and the v0.2.9 tag were updated with explicit old-ref leases in that authorized migration; that operation did not change repository visibility.
Existing clones must migrate safely rather than merging the old history back. Old objects may remain
in local reflogs, other clones or hosting caches; ref rewriting does not guarantee physical erasure.
See [other-Mac migration](OTHER_MAC_UPDATE.zh-CN.md). Do not publish old bundles or backups.

The release ZIP excludes .git and personal runtime state, so it can be reviewed/shared independently.
The scanner is heuristic, not a complete secret detector. It checks current tracked content or a
package, and optionally author/committer emails in history; it does not comprehensively scan every
historical blob or guarantee binary-image privacy. Public URLs/names identifying project maintainers
and upstream attribution are intentionally retained; local account/work information is not required.

## Functionality and optimization assessment

The current participation model has explicit enable/disable, per-conversation persistence,
temporary local override and mandatory one-off GPT consultation. Routine steps stay with Codex.
No need to introduce another mandatory prompt syntax or another planner loop.

Future improvements should be driven by evidence: measure end-to-end latency and handoff counts,
test across independent Macs and supported clients, and exercise restart/reconnect scenarios.
There is no measured fixed token saving, automatic host interception, universal natural-language
trigger accuracy, or native Windows support claim. Full remains project-bound and needs actual
ChatGPT file-read verification; a local state machine or screenshot is not that proof.
