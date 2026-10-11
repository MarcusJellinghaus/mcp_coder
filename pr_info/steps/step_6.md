# Step 6: `gh-tool get-base-branch` handles failed detection and documents the real order

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md`. Write the tests first, then the code. Run pylint, pytest (unit tests, `-n auto`) and mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/cli/commands/gh_tool.py`
- `tests/cli/commands/test_gh_tool.py`

## WHAT

`execute_get_base_branch(args: argparse.Namespace) -> int` — signature unchanged.

## HOW

- Replace `if base_branch == "unknown":` with `if base_branch is None:`.
- Warning text: `"Could not detect base branch from issue, PR, merge-base, or default"`.
- Docstring priority list, in code order:
  1. Linked issue's `### Base Branch` section
  2. Open PR base branch
  3. Git merge-base
  4. Default branch (main/master)

## ALGORITHM

```
base = detect_base_branch(project_dir)
if base is None: warn, return 1
print(base); return 0
```

## DATA

Exit codes unchanged: `0` printed branch, `1` not detected, `2` error.

## Tests (write first)

`test_gh_tool.py`:
- The test at line ~73 mocks `"unknown"`; change it to `None`, assert exit code `1` and that nothing is printed to stdout (`capsys`).
