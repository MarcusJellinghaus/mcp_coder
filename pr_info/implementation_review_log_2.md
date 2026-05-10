# Implementation Review Log — Issue #963

**Branch:** `963-vscodeclaude-implement-macos-linux-launch-support`
**Goal:** vscodeclaude: macOS/Linux launch support
**Started:** 2026-05-10

---

## Round 1 — 2026-05-10

(Run as round 2 in the supervisor cycle overall; round 1 of this `_log_2.md` invocation.)

**Findings** (from engineer subagent invoking `/implementation_review`):

1. Unknown POSIX platforms (e.g. FreeBSD) get no setup commands under the new `_SETUP_COMMAND_KEYS` lookup, where the previous `else: linux` branch would have used the Linux key. Behavior change for non-mainstream POSIX (`session_launch.py:67-71,168-174`).
2. Asymmetric fallbacks for unknown platforms across the three call sites — `_SETUP_COMMAND_KEYS.get(system, ())` vs. `_MCP_CONFIG_FILES.get(system, ".mcp.json")` — minor inconsistency.
3. `set -euo pipefail` makes the explicit `SESSION_ID` empty-check in `AUTOMATED_SECTION_POSIX` (`templates.py:284-289`) unreachable on the `mcp-coder prompt` failure path; trap fires instead.
4. POSIX path in `create_startup_script` re-checks `mcp_config_path.exists()` (`workspace.py:650-657`) even though `validate_mcp_json` runs upstream. Asymmetric with Windows.
5. Docstring at `workspace.py:508-510` advertises `Raises: FileNotFoundError: If the platform-specific MCP config file is absent.` — accurate for the POSIX branch but Windows branch never raises this directly.
6. `.mcp.linux.json` is byte-for-byte identical to `.mcp.macos.json` — intentional per the design summary, drift risk noted.
7. POSIX banner fields other than `title` (`{repo}`, `{status}`, `{issue_url}`, `{emoji}`) are interpolated raw inside single-quoted echo lines. Round 1 of the supervisor cycle already considered and rejected escaping these; reviewer agrees.

**Decisions**:

- **Skip #1** — Speculative per knowledge base ("If a change only matters when someone makes a future mistake, it's speculative"). The issue's decision table specifies Windows / Linux / Darwin only; mcp-coder isn't deployed on BSDs.
- **Skip #2** — Self-described as cosmetic / documenting-only.
- **Skip #3** — Reviewer's claim is partly wrong: the empty-check is NOT dead code. It still fires on the "command succeeded with empty output" path, which is its real purpose. The trap covers the "command failed" path. Both code paths are intended; removing the check would lose error detection on the empty-output case.
- **Skip #4** — Defensive code at a public function boundary is fine; protects direct callers outside `prepare_and_launch_session`. YAGNI cuts both ways here.
- **Skip #5** — Function-level docstring documents the contract (config absent → error). Whether Windows happens to delegate to upstream `validate_mcp_json` while POSIX raises directly is an internal mechanism detail. Splitting hairs not worth the diff.
- **Skip #6** — Intentional per design; flagged but already documented.
- **Skip #7** — Already triaged in round 1 of the supervisor cycle; reviewer concurs.

**Changes**: None. All findings triaged as Skip.

**Status**: no changes needed — review-clean.

---

## Final Status

**Supervisor cycle:** 2 rounds total.
- Round 1 (in `pr_info/implementation_review_log_1.md`): one Boy Scout fix accepted — `templates.py` module docstring updated for POSIX. Committed as `c52cd98`.
- Round 2 (this file): 7 minor findings, all triaged Skip (cosmetic / speculative / already-considered). Zero code changes.

**Quality gates after round 2:**
- `run_lint_imports_check`: PASSED (23 contracts kept, 0 broken).
- `run_vulture_check`: clean after a one-line whitelist addition. The new `setup_commands_macos` field on `RepoVSCodeClaudeConfig` (TypedDict, accessed via `dict.get(...)`) was added to `vulture_whitelist.py` next to its `setup_commands_linux` / `setup_commands_windows` siblings.

**Conclusion:** branch `963-vscodeclaude-implement-macos-linux-launch-support` is review-clean. No further engineering work required from the review supervisor.
