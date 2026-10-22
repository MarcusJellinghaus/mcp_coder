# Step 1 — Enable ruff `PLE2502` (covers bandit `B613`)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`). Implement step 1 only:
> add ruff rule `PLE2502` to `pyproject.toml` as specified below, run the checks, and produce exactly one commit.

## WHERE

- `pyproject.toml`, `[tool.ruff.lint] select` list (currently has `"PLW1510"` with its own comment).

## WHAT

No functions. Config change only. Insert directly after the `"PLW1510",` line:

```toml
    # PLE2502 bidirectional-unicode: covers bandit B613 (trojansource), which has no S port.
    "PLE2502",
```

## HOW

- Exact code only: do **not** add the `PL` prefix/group.
- `PLE2502` is stable, so `explicit-preview-rules` does not affect it.
- No changes to `ignore` or `per-file-ignores`.

## ALGORITHM

```
open pyproject.toml
find '"PLW1510",' in [tool.ruff.lint] select
insert comment line + '"PLE2502",' after it
run ruff check (src tests tools) -> expect 0 PLE2502 hits
run format, pylint, pytest, mypy -> all pass
commit
```

## DATA

None.

## Verification (serves as the test)

1. `mcp__mcp-tools-py__run_ruff_check(target_directories=["src", "tests", "tools"])` must pass.
   If it reports any `PLE2502` hit, write one line to `pr_info/.blocked.txt` naming the file(s) and stop.
2. `mcp__mcp-tools-py__run_format_code`
3. `mcp__mcp-tools-py__run_pylint_check`
4. `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`
5. `mcp__mcp-tools-py__run_mypy_check`

## Commit

`chore(ruff): enable PLE2502 to cover bandit B613 trojansource`
