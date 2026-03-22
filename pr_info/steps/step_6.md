# Step 6: Re-run Autofix Formatting

> **Context:** See [summary.md](summary.md). Steps 1–5 partially completed but introduced new formatting violations. This is a cleanup pass.

## Goal

Re-run `ruff check --fix` to resolve all auto-fixable violations (D212, D202) introduced by earlier steps.

## Rules Addressed

| Rule | Description |
|------|-------------|
| D212 | Multi-line summary not on first line |
| D202 | Blank line after function docstring |

## Discovery

```bash
ruff check src tests --select D212,D202
```

## HOW

```bash
# 1. Auto-fix
ruff check --fix src tests

# 2. Re-format
./tools/format_all.sh

# 3. Verify these rules are resolved
ruff check src tests --select D212,D202
```

## Verification

- `ruff check src tests --select D212,D202` — 0 violations
- `pytest -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all pass

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md for context.

Execute step 6: Re-run autofix formatting.

1. Run `ruff check src tests --select D212,D202` to see current violations
2. Run `ruff check --fix src tests` to auto-fix
3. Run `./tools/format_all.sh`
4. Verify with `ruff check src tests --select D212,D202` — must be 0
5. Run pylint, pytest, mypy checks
6. Commit the changes
```
