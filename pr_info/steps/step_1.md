# Step 1 — Marker definitions and `-m` filters (config, CI, tooling)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Remove `claude_api_integration`, `formatter_integration` and `github_integration`
> from the marker definitions and `-m` filters listed below. Run the precondition
> check first. Then make the edits, run the checks, and make one commit.

## Precondition (acts as the test)

Run:

```
mcp__mcp-tools-py__run_pytest_check(extra_args=["--collect-only", "-q", "-m", "claude_api_integration or formatter_integration or github_integration"])
```

Expected: 0 tests selected (all deselected). This proves that removing the markers
from any `-m` expression can't change CI selection.
If any test is selected: write one line to `pr_info/.blocked.txt` naming the selected test, and stop.

## WHERE / WHAT

### `pyproject.toml` (`[tool.pytest.ini_options]`)
- Delete the marker lines `"claude_api_integration: ..."` and `"github_integration: ..."`.
- In the `# RECOMMENDED usage patterns:` comment:
  - Replace the line `# -m "not claude_cli_integration and not claude_api_integration ... - All unit tests (explicit)` with
    `# Unit tests only: see the marker filter in .claude/CLAUDE.md`
  - Delete `# -m "claude_api_integration"` and `# -m "github_integration"`.

### `.github/workflows/ci.yml`
- Unit job (line ~156): in the `-m '...'` expression, delete only `and not claude_api_integration`, `and not formatter_integration` and `and not github_integration`. The result must be the CI unit-job set from the summary. Nothing else on the line changes.
- Integration job (line ~188): `-m 'git_integration or formatter_integration or github_integration or install_integration'` becomes `-m 'git_integration or install_integration'`.

### `.claude/CLAUDE.md`
- The fast unit-test command (line ~77): set the `-m` string to the CLAUDE.md set from the summary.
- The `Markers:` line (~83) becomes:
  `` Markers: `git_integration`, `claude_cli_integration`, `copilot_cli_integration`, `install_integration`, `jenkins_integration`, `langchain_integration`, `llm_integration`, `textual_integration`. ``

### `.run/pytest in tests - just unit tests.run.xml`
- In the `_new_additionalArguments` value, replace the expression between `\&quot;` and `\&quot;` with the CLAUDE.md set. Keep `-n auto --durations=20 -m` and the escaping exactly as they are.

### `tools/get_pytest_performance_stats.bat`
- Line ~62 (unit tests): set the `-m "..."` value to the CLAUDE.md set.
- Delete these three whole sections, each running from its `REM ...` line through the two trailing `call :echo_both " "` lines:
  - `REM Claude API Integration Tests`
  - `REM Formatter Integration Tests`
  - `REM GitHub Integration Tests`
- Renumber the headers that remain: UNIT `[1/3]`, CLAUDE CLI `[2/3]`, GIT `[3/3]`. Don't add new sections.

### `tools/ci_coverage_summary.py`
- `MARKER_TRAP_CAVEAT`: remove `` `claude_api_integration`, `` and re-wrap the string literals:

```python
MARKER_TRAP_CAVEAT = (
    "_Markers excluded in CI (`claude_cli_integration`, "
    "`copilot_cli_integration`, `jenkins_integration`, `llm_integration`, "
    "`textual_integration`) never run here, so lines only reachable under them "
    "show as uncovered._"
)
```

Leave the wrong `jenkins_integration` claim as it is; that's #1356.
`tests/tools/test_ci_coverage_summary.py` checks only that the constant appears in the output, so no test change is needed.

## HOW / ALGORITHM / DATA

No new functions, imports or data structures. Text edits only.

## Checks, then commit

1. Run `mcp__mcp-tools-py__run_format_code`.
2. Run pylint, mypy, and the unit tests using the **new** CLAUDE.md command (`-n auto`).
3. Search `pyproject.toml`, `.github/`, `.claude/`, `.run/` and `tools/` for `claude_api_integration|formatter_integration|github_integration`. Expect 0 hits.
4. Commit once, e.g. `chore(tests): drop unused pytest markers from config, CI and tooling`.
