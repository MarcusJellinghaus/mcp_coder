# Plan Review Log — Issue #922

Branch: 922-add-cross-repo-ci-listen-to-all-3-upstreams-add-typecheck-extra-fixes-latent-mypy-bug
Started: 2026-04-28

## Round 1 — 2026-04-28

**Findings:**
- [F-A1] (escalated) Latent mypy unreachable bug at `src/mcp_coder/utils/tui_preparation.py:121` not addressed in any step; branch name promised the fix; step verifications would fail.
- [F-A2] (skipped) Self-referential `mcp-coder[types]` install — user already chose this wording in the issue body; left as-is.
- [F-B1] (accepted) `step_1.md` verification doesn't actually install the new `[typecheck]` extra — only checks toml string contents.
- [F-B2] (accepted) `step_2.md` verification's `import yaml` sanity check uses a dependency (`pyyaml`) not present in any repo extra.
- [F-B3] (accepted) `step_*.md` pytest invocations exclude only 6 markers; CLAUDE.md canonical list has 10.
- [F-C1, F-C2] (informational) Acceptance criteria 4–6 and `no-url-deps` matrix entry — out of scope, no action.

**Decisions:**
- F-A1: user chose to fix the bug pre-implementation as a separate commit on this branch. Resolved by commit `ebd92e0`. F-A1 dropped from plan changes.
- F-A2: not escalated; matches issue text.
- F-B1, F-B2, F-B3: auto-accepted.

**User decisions:**
- Q: How to handle F-A1 (latent mypy bug)? A: Fix it now in a separate commit on this branch, before plan execution. Done as commit `ebd92e0`.

**Changes:**
- `pr_info/steps/step_1.md`: added explicit `pip install -e .[typecheck]` verification step.
- `pr_info/steps/step_2.md`: replaced/removed `import yaml` sanity check.
- `pr_info/steps/step_1.md`, `step_2.md`, `step_3.md`: aligned pytest marker exclusion lists to the canonical 10-marker set.
- `pr_info/steps/summary.md`: added a Notes section recording the pre-implementation mypy fix (commit `ebd92e0`).

**Status:** changes applied; not yet committed (supervisor will instruct commit agent).

## Round 2 — 2026-04-28

**Findings:**
- [F-B1] (accepted) `step_3.md` Change 2 `old_string` is identical to a snippet in the `architecture` job of `ci.yml` — non-unique match would break `mcp__workspace__edit_file`.
- [F-C1] (informational) `formatter_integration` marker not registered in `pyproject.toml [tool.pytest.ini_options].markers` — pre-existing repo inconsistency, out of scope of #922.

**Decisions:**
- F-B1: auto-accepted; expanded `old_string` to anchor on the unique `no-url-deps` matrix entry above the install step (after first considering — and rejecting — the `name: ${{ matrix.check.name }}` line, which appears in both jobs, and the trailing `Run ${{ matrix.check.name }}` step, which is also identical in both jobs).
- F-C1: noted, not actioned.

**User decisions:** none.

**Changes:**
- `pr_info/steps/step_3.md`: Change 2 `old_string`/`new_string` extended to include the `no-url-deps` matrix entry through the install step (the `Install latest GitHub dependencies` block, `Install uv`, `Set up Python 3.11`, etc. fall in between) so the match is unique within `ci.yml`. Added a clarifying note explaining why simpler anchors (the install step alone, or with `name: ${{ matrix.check.name }}`, or with the trailing `Run` step) are non-unique. Also updated the `## HOW` bullet to reflect the new disambiguation strategy.

**Status:** changes applied; not yet committed.

## Final Status

**Rounds run:** 3 (round 3 produced zero actionable findings).
**Pre-implementation fix landed:** commit `ebd92e0` — `fix(tui): resolve mypy unreachable warning in macOS terminal probe` (restructured the platform guard in `_check_macos_terminal_app` so mypy strict-mode no longer flags `tui_preparation.py:121` as unreachable). This was scope F-A1 from round 1, escalated and resolved out-of-band before any plan step ran.

**Plan changes accumulated across rounds 1–2:**
- `pr_info/steps/step_1.md` — added explicit `pip install -e .[typecheck]` smoke test in Verification; aligned pytest marker exclusion list to canonical 10 markers.
- `pr_info/steps/step_2.md` — replaced `import yaml` sanity check with stdlib-only `name:` header check; aligned pytest markers.
- `pr_info/steps/step_3.md` — extended Change 2 `old_string`/`new_string` to anchor on the unique `no-url-deps` matrix entry (only unique anchor in `ci.yml`'s `test` job); added `**Note:**` paragraph documenting the disambiguation; aligned pytest markers.
- `pr_info/steps/summary.md` — added Notes section recording the pre-implementation mypy fix in commit `ebd92e0`.

**Verdict:** plan ready for approval. Source code (post-`ebd92e0`) is clean: mypy ✓, pylint ✓, pytest 3672 passed.
