# Step 2 — Smoke-test skip text points to PROJECT

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`
> exactly. Step 1 (the PROJECT `.mcp-file-access` row) is already committed.
> TDD: update the test first, see it fail, then implement. Run the checks
> listed below; all must pass. One commit.

## Precondition

`_file_access_row` exists in `src/mcp_coder/cli/commands/verify_sections.py`
(step 1). If it does not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `tests/cli/commands/test_verify_mcp_edit_smoke.py`
- `src/mcp_coder/cli/commands/verify.py`
- `docs/cli-reference.md`

## 1. Test first — `test_verify_mcp_edit_smoke.py`

In `test_smoke_test_skipped_when_rules_file_invalid`:

- Docstring: `"""An invalid rules file skips the smoke test and points to PROJECT."""`
- Replace the two value assertions (`"skipped: invalid rules file"` and
  `"unknown level 'writable'"`) with
  `assert result.value == "skipped: invalid .mcp-file-access (see PROJECT)"`.
- Keep the `[WARN]` marker and `mock_prompt_llm.assert_not_called()` assertions.

Run it — it fails.

## 2. Implementation — `verify.py`

### WHAT

`_smoke_test_skip_reason(project_dir: Path) -> str | None` — signature
unchanged.

### ALGORITHM (only the invalid-file branch changes)

```
if not FILE_ACCESS_SUPPORTED: gitignore-only fallback (unchanged)
if validate_access_rules(project_dir):
    return "skipped: invalid .mcp-file-access (see PROJECT)"
access = get_file_access(...)  (unchanged)
```

Drop the `problems` variable; the problem list now appears only in the PROJECT
row. Imports stay (`validate_access_rules` is still used).

### DATA

Returns the skip text or None, as before.

## 3. Docs — `docs/cli-reference.md`

Replace the sentence "The smoke test is skipped with a warning when
`.mcp-file-access` is invalid or leaves `.scratch/` hidden or read-only for MCP."
with "The smoke test is skipped with a warning when `.mcp-file-access` leaves
`.scratch/` hidden or read-only for MCP, or is invalid (the problems are listed
in the project section)."

## Checks

1. `run_pytest_check(extra_args=["-n", "auto", "tests/cli/commands/test_verify_mcp_edit_smoke.py"])`.
2. Fast unit suite (marker filter from `.claude/CLAUDE.md`), pylint, mypy.
3. `run_format_code`, then commit:
   `feat(verify): point the smoke-test skip for an invalid .mcp-file-access to PROJECT`
