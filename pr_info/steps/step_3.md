# Step 3 — Move `generate_commit_message_with_llm` classes from `test_commit.py` to `test_commit_operations_default_args.py`

## LLM prompt

> Read `pr_info/steps/summary.md` (hard rules, standard checks) and implement
> `pr_info/steps/step_3.md` exactly. Pure refactoring: move code with `move_symbol` only,
> edit only imports. Produce exactly one commit.

## WHERE

- Source: `tests/cli/commands/test_commit.py`
- Destination (new): `tests/workflow_utils/test_commit_operations_default_args.py`

## WHAT

| Symbol | Kind | Tests |
|---|---|---:|
| `TestGenerateCommitMessageWithLLM` (the one in `test_commit.py`) | class | 4 |
| `TestGenerateCommitMessageWithLLMExtended` | class | 6 |

Both call `generate_commit_message_with_llm(project_dir)` with default args. The same-named
class in `tests/workflow_utils/test_commit_operations.py` must not be touched.

## HOW

- One call, `source_file` explicit (two `TestGenerateCommitMessageWithLLM` exist in the repo):
  `mcp__mcp-tools-py__move_symbol(source_file="tests/cli/commands/test_commit.py", symbol_names=["TestGenerateCommitMessageWithLLM", "TestGenerateCommitMessageWithLLMExtended"], dest_file="tests/workflow_utils/test_commit_operations_default_args.py", dry_run=true)`, then apply.
- Expected imports afterwards:
  - `test_commit.py`: `argparse`, `logging`, `Path`, `Mock`, `patch`, `pytest`,
    `from mcp_coder.cli.commands.commit import _push_after_commit, execute_commit_auto, validate_git_repository`,
    `create_parser`. The `mcp_coder.workflow_utils.commit_operations` import is **gone
    entirely** (remaining classes use it only as `@patch` target strings).
  - `test_commit_operations_default_args.py`: `Path`, `Mock`, `patch`,
    `from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm`.
    No `pytest`, no `logging`.

## ALGORITHM

```
before = collect-only counts: test_commit.py, tests/cli/commands/, tests/workflow_utils/
move_symbol dry run -> touches test_commit_operations.py or any file besides source/dest: write one line to pr_info/.blocked.txt and stop
move_symbol apply; read both file headers; fix imports (ruff_fix F401 with target_directories=["tests/cli/commands/test_commit.py", "tests/workflow_utils/test_commit_operations_default_args.py"] / add missing)
run standard checks; compare counts to DATA
```

## DATA — expected counts (collect-only, no marker filter)

| Path | Before | After |
|---|---:|---:|
| `tests/cli/commands/test_commit.py` | 40 | 30 |
| `tests/workflow_utils/test_commit_operations_default_args.py` | — | 10 |
| `tests/workflow_utils/test_commit_operations.py` | 19 | 19 |
| `tests/cli/commands/` | C (record) | C − 10 |
| `tests/workflow_utils/` | W (record) | W + 10 |

`test_commit.py` (~855 lines) stays allowlisted. Count mismatch → write one line to
`pr_info/.blocked.txt` and stop.

## Commit

`test(commit): move generate_commit_message_with_llm tests to workflow_utils`
