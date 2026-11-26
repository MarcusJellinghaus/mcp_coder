# Step 7: finalisation formats before its commit

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest
> set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/implement/finalisation.py`: `run_finalisation`
- `tests/workflows/implement/test_finalisation_format.py` (new)

## WHAT

One line in `run_finalisation`, after the empty-response check (step 3) and
before the `get_full_status` "changes to commit" check (step 4):

```python
format_best_effort(project_dir, "finalisation commit")
```

## HOW

- Import `format_best_effort` from `mcp_coder.workflow_steps.commit` (next to
  `push_changes`).
- The formatter runs after `read_and_clear_blocked` (already in the `finally`
  around `prompt_llm`) and before the changes check. A tree the formatter
  alone changed is therefore committed too.
- Renumber the inline step comments if needed.

## ALGORITHM

```
prompt_llm(...) ; read_and_clear_blocked
if empty response: return False
format_best_effort(project_dir, "finalisation commit")
status = get_full_status(...); if clean: return True
commit message (file -> LLM -> default); commit_all_changes; push_changes
```

## DATA

Unchanged: returns `bool`.

## Tests first (`test_finalisation_format.py`)

Patch the finalisation externals the way `test_finalisation.py` does
(`has_incomplete_work`, `prepare_llm_environment`, `get_branch_name_for_logging`,
`bash_grants_of` / `llm_permissions`, `get_prompt`, `fill_prompt` /
`resolve_prompt_slots`, `prompt_llm`, `store_session`, `get_full_status`,
`generate_commit_message_with_llm`, `commit_all_changes`, `push_changes`):

- `formatter_mocks.format_best_effort` is called with `project_dir` before
  `get_full_status` and before `commit_all_changes` (recorded order).
- Empty LLM response: returns False and the formatter is not called.
- Real helper restored (`monkeypatch.setattr(finalisation,
  "format_best_effort", commit.format_best_effort)`), `commit.run_formatters`
  raising `FormatterConfigError` (second case: returning False): WARNING
  logged, `commit_all_changes` still called, result True.

## Commit

`feat(implement): format before the finalisation commit`
