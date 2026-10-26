# Step 8 — Banner cleanup, allowlist, final verification

## LLM prompt
> Read `pr_info/steps/summary.md` and this file, `pr_info/steps/step_8.md`. Implement step 8 only: delete the eleven
> section-banner comment lines listed below from `tests/icoder/test_app_pilot.py`, remove its entry from
> `.large-files-allowlist`, then run the full verification. Make exactly one commit.

## WHERE
- `tests/icoder/test_app_pilot.py`
- `.large-files-allowlist`

## WHAT
Delete these comment lines (match them by text). Delete the comment line only; the formatter handles blank lines.
- Eight with no code left under them:
  - `# --- Streaming edge-case regression tests (f–h) ---`
  - `# --- BusyIndicator integration tests ---`
  - `# --- Plain text rendering tests (Step 3) ---`
  - `# --- Cancel / Escape key tests ---`
  - `# --- Step 9: append_unit migration (clickable units + orphan cleanup) ---`
  - `# --- #1046 step 2: ApprovalModal pushed directly (no stream wiring yet) ---`
  - `# --- #1046 step 5: persist choice writes .icoder/settings.local.json ---`
  - `# --- Step 10: shutdown hook + closed-app guard (R9) ---`
- Three that went stale:
  - `# --- Streaming buffer regression tests (a–e + edge cases) ---`
  - `# --- Step 9: approval_request branch + the direct UI -> engine cancel channel ---`
  - `# --- #1046 step 3: modal pushed from the stream + once/session scopes applied ---`
- **Keep:** the `Status bar widget tests` banner, `Step 3: skill_name threading + permission_warning render`, and
  `Step 5: startup permission notices …`.

Then remove the line `tests/icoder/test_app_pilot.py` from `.large-files-allowlist`.

If the remaining banners don't match the 3 kept plus the 11 to delete, write one line to `pr_info/.blocked.txt` and stop.

## HOW
No code changes. Only comments in the base file and one allowlist line change.

## ALGORITHM
```
search_files(pattern="^# ---", glob="tests/icoder/test_app_pilot.py") -> classify each banner as keep / delete
delete the 11 lines; remove the allowlist entry
run_format_code
run the full verification below
```

## DATA — full verification (all must pass)
- `run_ruff_check`, `run_pylint_check`, `run_mypy_check`, `run_lint_imports_check`, `run_tach_check`, `run_vulture_check`
- `check_file_size` passes, with no stale allowlist entry; all 7 files are under 750 lines
- `--collect-only -q` per file: `test_app_pilot.py` 19, `_streaming` 20, `_cancel` 5, `_content_units` 16,
  `_approval` 22, `_approval_persist` 11, `_shutdown` 3; `tests/icoder/` and whole suite equal the baseline counts recorded in step 1
- `run_pytest_check(extra_args=["-q", "-n", "auto", "tests/icoder/"], timeout_seconds=600)`: everything that passed at baseline passes
- The fast unit suite from CLAUDE.md with `-n auto` passes
- `-m "not textual_integration"` on each of the 7 files gives "No Tests Found"
- `search_files(pattern="(test_app_pilot\\w*|conftest)\\.(?!py\\b)\\w", glob="tests/icoder/**/*.py")` finds 0 matches
- Compact diff against the base branch (`mcp__mcp-workspace__git` diff, `compact=true`). The only non-moved hunks allowed are:
  - import changes
  - the new file headers
  - the six `pytestmark` lines, plus `import pytest` in `_cancel`
  - the eleven deleted banners
  - the allowlist line
  - blank lines

  Anything else: write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(icoder): drop stale banners and allowlist entry for test_app_pilot (#1323)`
