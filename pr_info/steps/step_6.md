# Step 6 — PR summary diff excludes all of `pr_info/`

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` exactly.
> Update the test first, then the code. Run pylint, pytest (fast unit set, `-n auto`) and mypy; all must pass.
> Format the code and make exactly one commit for this step.

## WHERE
- `src/mcp_coder/workflows/create_pr/core.py` — `generate_pr_summary`
- `tests/workflows/create_pr/test_generation.py` (~line 46)

## WHAT
```python
diff_content = get_branch_diff(
    project_dir, base_branch=base_branch, exclude_paths=["pr_info/"]
)
```

## HOW
`pr_info/` is deleted before the PR exists, so none of it belongs in the summary.

## Tests
- Change the asserted `exclude_paths` in `test_generation.py` to `["pr_info/"]`.

## DATA
None.
