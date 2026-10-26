# Step 1 — Move `TestStripClaudeFooters` to `test_commit_operations_parsing.py`

## LLM prompt

> Read `pr_info/steps/summary.md` (hard rules, standard checks) and implement
> `pr_info/steps/step_1.md` exactly. Pure refactoring: move code with `move_symbol` only,
> edit only imports and `.large-files-allowlist`. Produce exactly one commit.

## WHERE

- Source: `tests/workflow_utils/test_commit_operations.py`
- Destination (new): `tests/workflow_utils/test_commit_operations_parsing.py`
- `.large-files-allowlist`

## WHAT

| Symbol | Kind | Tests |
|---|---|---:|
| `TestStripClaudeFooters` | class (tests `strip_claude_footers` and `parse_llm_commit_response`) | 21 |

No functions are created or changed.

## HOW

- `mcp__mcp-tools-py__move_symbol(source_file="tests/workflow_utils/test_commit_operations.py", symbol_names=["TestStripClaudeFooters"], dest_file="tests/workflow_utils/test_commit_operations_parsing.py", dry_run=true)`, then the same call with `dry_run=false`.
- Expected imports afterwards:
  - `test_commit_operations.py`: `logging`, `Path`, `Mock`, `patch`, `pytest`,
    `ClaudeAPIError`, `generate_commit_message_with_llm`, `parse_llm_commit_response`
    (`strip_claude_footers` dropped).
  - `test_commit_operations_parsing.py`: only
    `from mcp_coder.workflow_utils.commit_operations import parse_llm_commit_response, strip_claude_footers`.
- `.large-files-allowlist`: delete the line `tests/workflow_utils/test_commit_operations.py`.

## ALGORITHM

```
before = collect-only counts: test_commit_operations.py, tests/workflow_utils/
move_symbol dry run -> if it touches files other than source/dest: write one line to pr_info/.blocked.txt and stop
move_symbol apply; read both file headers; fix imports (ruff_fix F401 with target_directories=["tests/workflow_utils/test_commit_operations.py", "tests/workflow_utils/test_commit_operations_parsing.py"] / add missing)
remove allowlist entry
run standard checks; compare counts to DATA
```

## DATA — expected counts (collect-only, no marker filter)

| Path | Before | After |
|---|---:|---:|
| `tests/workflow_utils/test_commit_operations.py` | 40 | 19 |
| `tests/workflow_utils/test_commit_operations_parsing.py` | — | 21 |
| `tests/workflow_utils/` | N (record) | N |

`test_commit_operations.py` is ~655 lines afterwards (under 750). Count mismatch or a file
still ≥ 750 lines → write one line to `pr_info/.blocked.txt` and stop.

## Commit

`test(workflow_utils): move TestStripClaudeFooters to test_commit_operations_parsing.py`
