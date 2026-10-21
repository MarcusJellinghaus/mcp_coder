# Step 1 — Enable ruff `UP` and apply the fixes

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Use the MCP tools only (`run_ruff_check`, `run_ruff_fix`, `run_format_code`,
> `run_mypy_check`, `run_pylint_check`, `run_pytest_check`). Do not hand-audit
> annotation sites. Make one commit when all checks pass.

## WHERE

- `pyproject.toml`: the `[tool.ruff.lint] select` list
- `src/mcp_coder/**/*.py`, `tests/**/*.py`: autofix targets (the tool's default scope)
- `src/mcp_coder/workflows/vscodeclaude/types.py`: `LivenessRule`, `SessionAction`
- `tests/workflows/review/test_gates.py`: `_UnlistedCIStatus` (inside the "unlisted CIStatus" test)

## WHAT

No new functions. The only changes are configuration and mechanical rewrites:

```toml
select = [
    ...,
    "C4", "B",
    "S",
    "UP",
]
```

```python
from enum import StrEnum

class LivenessRule(StrEnum): ...
class SessionAction(StrEnum): ...
```

```python
class _UnlistedCIStatus(StrEnum):
    """Hashable str enum standing in for a future CIStatus member."""
```

## HOW

1. **Precondition / test-first (red):** `run_ruff_check(select=["UP"], max_issues=0)`.
   It is expected to report findings, only from the 10 rules listed in the summary.
   If it reports a UP rule that is not in that list, write one line to
   `pr_info/.blocked.txt` and stop.
2. Add `"UP"` to `select` in `pyproject.toml`, as shown above. Add no comment and no
   `ignore` entry.
3. Safe fixes: `run_ruff_fix(select=["UP", "F401"])`.
4. Unsafe fix, UP042 only, as a separate run:
   `run_ruff_fix(select=["UP042", "F401"], extra_args=["--unsafe-fixes"])`.
   Do not merge steps 3 and 4 into one run: that would apply unsafe fixes for every rule.
5. Replace the `_UnlistedCIStatus` docstring with the one shown above (the old one
   claims it mirrors "the real enum").
6. `run_format_code`.
7. Verify (green):
   - `run_ruff_check()` (project config) reports 0 issues. If UP findings remain
     after the autofix runs, fix them by hand (issue step 3: "or by hand"). Write
     one line to `pr_info/.blocked.txt` and stop only for a site that cannot be
     fixed without adding a `noqa` comment or an `ignore` entry. Never add either.
   - `run_mypy_check()` is clean.
   - `run_pylint_check()` is clean.
   - `run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])` is green.
   - Integration suite: `run_pytest_check(extra_args=["-n", "auto"])` with no marker
     filter is green. If a failure is environmental (missing credentials or service)
     and also happens on `main`, note it in the PR, not in a file.
8. Search the diff for `noqa: UP` (`git diff` with `search="noqa: UP"`). It must find nothing.
9. Commit: `build(ruff): enable UP (pyupgrade) rules (#1166)`.

## ALGORITHM

```
assert ruff(select=UP) reports only the 10 known rules     # red
add "UP" to select
ruff --fix --select UP,F401                                # 526 safe fixes
ruff --fix --unsafe-fixes --select UP042,F401              # 3 StrEnum sites
fix test docstring; format
assert ruff, mypy, pylint, pytest (unit + integration) clean  # green
```

## DATA

There are no new data structures. `LivenessRule` and `SessionAction` keep the same
member names and values. Only their base class changes, to `StrEnum`.

## Acceptance (from #1166)

- `ruff check src tests` is clean with `UP` selected, including UP042, and there are
  no new F401 findings.
- mypy `--strict` is clean on `src` and `tests`, and pylint is clean.
- The full unit + integration suite is green.
- No `# noqa: UP*` is added, and no `UP*` entry is added to `ignore`.
