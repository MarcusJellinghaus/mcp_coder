# Step 2 — Move `TestParseLLMCommitResponse` from `test_commit.py` to `test_commit_operations_parsing.py`

## LLM prompt

> Read `pr_info/steps/summary.md` (hard rules, standard checks) and implement
> `pr_info/steps/step_2.md` exactly. Pure refactoring: move code with `move_symbol` only,
> edit only imports. Produce exactly one commit.

## Precondition

`tests/workflow_utils/test_commit_operations_parsing.py` exists (step 1) and contains no
`TestParseLLMCommitResponse`. If not → write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Source: `tests/cli/commands/test_commit.py`
- Destination: `tests/workflow_utils/test_commit_operations_parsing.py`

## WHAT

| Symbol | Kind | Tests |
|---|---|---:|
| `TestParseLLMCommitResponse` (the one in `test_commit.py`) | class (tests `parse_llm_commit_response`) | 4 |

The same-named class in `tests/workflow_utils/test_commit_operations.py` stays where it is.

## HOW

- `mcp__mcp-tools-py__move_symbol(source_file="tests/cli/commands/test_commit.py", symbol_names=["TestParseLLMCommitResponse"], dest_file="tests/workflow_utils/test_commit_operations_parsing.py", dry_run=true)`, then apply.
- Expected imports afterwards:
  - `test_commit.py`: the `commit_operations` import keeps only
    `generate_commit_message_with_llm` (`parse_llm_commit_response` dropped); everything else
    unchanged.
  - `test_commit_operations_parsing.py`: still only
    `from mcp_coder.workflow_utils.commit_operations import parse_llm_commit_response, strip_claude_footers`
    (no `pytest`, `Mock`, `Path`). Class order: `TestStripClaudeFooters`, then
    `TestParseLLMCommitResponse`.

## ALGORITHM

```
before = collect-only counts: test_commit.py, tests/cli/commands/, tests/workflow_utils/
move_symbol dry run -> touches test_commit_operations.py or any file besides source/dest: write one line to pr_info/.blocked.txt and stop
move_symbol apply; read both file headers; fix imports (ruff_fix F401 with target_directories=["tests/cli/commands/test_commit.py", "tests/workflow_utils/test_commit_operations_parsing.py"] / add missing)
run standard checks; compare counts to DATA
```

## DATA — expected counts (collect-only, no marker filter)

| Path | Before | After |
|---|---:|---:|
| `tests/cli/commands/test_commit.py` | 44 | 40 |
| `tests/workflow_utils/test_commit_operations_parsing.py` | 21 | 25 |
| `tests/cli/commands/` | C (record) | C − 4 |
| `tests/workflow_utils/` | W (record) | W + 4 |

`test_commit.py` stays allowlisted (still > 750 lines). Count mismatch → write one line to
`pr_info/.blocked.txt` and stop.

## Commit

`test(commit): move parse_llm_commit_response tests to workflow_utils`
