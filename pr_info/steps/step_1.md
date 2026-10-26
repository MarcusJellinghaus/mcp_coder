# Step 1 — Split `TestSessionRestart` by inserting four class headers

## LLM prompt
> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_1.md`) exactly.
> This is a pure refactoring: only the four 2-line class headers below may be added. Don't edit any `def` line, method body, decorator or indentation, and don't edit the existing `class TestSessionRestart:` header or its docstring.
> Use MCP tools only. Finish with the standard checks from the summary, then make one commit.

## WHERE
- `tests/workflows/vscodeclaude/test_session_restart.py` (only file touched)

## WHAT
Four `mcp__mcp-workspace__edit_file` calls. In each one:
- `old_string` is the unique `def` line named below, 4-space indented, including the trailing `(`.
- `new_string` is the header, then a blank line, then that same `def` line unchanged.

| # | Header goes directly above | Header text (column 0, verbatim) |
|---|---|---|
| a | `    def test_prepare_and_launch_session_success(` | `class TestPrepareAndLaunchSession:` / `    """Tests for prepare_and_launch_session() success and failure cleanup."""` |
| b | `    def test_process_eligible_issues_respects_max_sessions(` | `class TestProcessEligibleIssuesMaxSessions:` / `    """Tests for the max_sessions limit in process_eligible_issues()."""` |
| c | `    def test_restart_closed_sessions_removes_orphans(` | `class TestRestartClosedSessionsLifecycle:` / `    """Tests for orphan, liveness and relaunch handling in restart_closed_sessions()."""` |
| d | `    def test_restart_closed_sessions_skips_blocked_issues(` | `class TestRestartClosedSessionsIssueStatus:` / `    """Tests for issue-status gating in restart_closed_sessions()."""` |

Shape of each `new_string` (shown for a):
```text
class TestPrepareAndLaunchSession:
    """Tests for prepare_and_launch_session() success and failure cleanup."""

    def test_prepare_and_launch_session_success(
```
`run_format_code` fixes the blank lines (two before each class).

## HOW
- None of the four `def` lines has a decorator, so each header goes directly above its `def` line.
- `TestSessionRestart` becomes a class with only a docstring. It goes away when the file is deleted in step 5.

## ALGORITHM
```
baseline: collect-only (no marker filter) on directory -> record N; test_session_restart.py -> 16; test_session_launch_process_issues.py -> 6
baseline: pytest -v on test_session_restart.py + test_session_launch_process_issues.py -> 22 passed (16 + 6)
for each of a..d: edit_file(old=def line, new=header + blank + def line)
run_format_code
gate: list_symbols -> exactly 6 symbols; pytest -v on file -> 16 passed, split 3/1/5/7 by class
standard checks; commit
```

## DATA / gates
- **Collect-only baselines (before editing, no marker filter).** Record each actual result in the `## Recorded baseline` section at the end of this file. Later steps compare against these numbers:
  - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/"])`: expected **688** on 2026-10-26. Record the actual value; later steps use it as the directory baseline.
  - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/test_session_restart.py"])` → **16**
  - `run_pytest_check(extra_args=["--collect-only", "-q", "tests/workflows/vscodeclaude/test_session_launch_process_issues.py"])` → **6**
  - If either file count differs: write one line to `pr_info/.blocked.txt` and stop.
- **Baseline (before editing):** `run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart.py", "tests/workflows/vscodeclaude/test_session_launch_process_issues.py"])` → **22 passed** (16 + 6). If not: write one line to `pr_info/.blocked.txt` and stop.
- **`list_symbols("tests/workflows/vscodeclaude/test_session_restart.py")`** shows exactly these six: `_make_assessment`, `TestSessionRestart`, `TestPrepareAndLaunchSession`, `TestProcessEligibleIssuesMaxSessions`, `TestRestartClosedSessionsLifecycle`, `TestRestartClosedSessionsIssueStatus`.
- **`run_pytest_check(extra_args=["-v", "tests/workflows/vscodeclaude/test_session_restart.py"])`** → **16 passed**. Counted from the `::<Class>::` node IDs, the split is **3 / 1 / 5 / 7** in the order a / b / c / d.
- **Directory collect-only** → the recorded directory baseline.
- **Compact diff:** only the four added 2-line headers plus blank lines.
- **If any gate fails:** remove the four inserted headers with `edit_file`, write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(vscodeclaude): split TestSessionRestart into four classes`

## Recorded baseline
Filled in during step 1, before editing:
- `tests/workflows/vscodeclaude/` collect-only: 688
- `test_session_restart.py` collect-only: 16
- `test_session_launch_process_issues.py` collect-only: 6
