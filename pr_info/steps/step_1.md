# Step 1: Autofix Formatting

> **Context:** See [summary.md](summary.md) for overall plan. This is step 1 of 5.

## Goal

Fix all auto-fixable docstring formatting violations using `ruff check --fix`.

## Rules Addressed

| Rule | Count | Description |
|---|---|---|
| D200 | ~1 | Unnecessary multiline docstring |
| D202 | ~10 | Blank line after function docstring |
| D205 | ~3 | Missing blank line after summary |
| D209 | ~1 | Newline after last paragraph |
| D212 | ~54 | Multi-line summary not on first line |
| D301 | ~6 | Use raw string for backslashes |

**Total:** ~75 auto-fixes

## WHERE

All `.py` files under `src/` and `tests/` that have formatting violations.

## WHAT

No new functions. This is a formatting-only change.

## HOW

```bash
# 1. Run ruff autofix
ruff check --fix src tests

# 2. Run format_all to ensure black/isort consistency
./tools/format_all.sh

# 3. Verify remaining violations decreased
ruff check src tests --statistics
```

## ALGORITHM

```
1. Run `ruff check --fix src tests` (applies all safe auto-fixes)
2. Run `./tools/format_all.sh` (black + isort re-format)
3. Run ruff check to verify formatting rules are resolved
4. Run pylint, pytest, mypy to verify no regressions
5. Commit
```

## DATA

No data structures. Output: modified `.py` files with corrected docstring formatting.

## Verification

- `ruff check src tests` — D200, D202, D205, D209, D212, D301 counts should drop to 0
- `pytest -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all pass
- `mypy --strict src tests` — no regressions

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Execute step 1: Autofix docstring formatting.

1. Run: ruff check --fix src tests
2. Run: ./tools/format_all.sh
3. Verify with ruff check, pylint, pytest, mypy — all must pass
4. Commit the changes
```
