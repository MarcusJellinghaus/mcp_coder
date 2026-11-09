# Step 4 — Implement fix loop uses the toolkit's `fix.check`

See `pr_info/steps/summary.md` ("Implement fix loop"). Requires Step 1.

## LLM prompt

> Implement Step 4 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_4.md`.
> Write the tests first. Keep session names (`step_N_mypy_K`), log messages and the loop's
> retry logic unchanged (#1389 / #1199). Run pylint, mypy and pytest; all must pass.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py` (`check_and_fix_mypy`)
- `src/mcp_coder/prompts/prompts.md` (delete section "Mypy Type Fixes" incl. "Mypy Fix
  Prompt" and `[mypy_output]`)
- `docs/processes-prompts/processes/05-implementation.md`
- Tests: `tests/workflows/implement/test_task_processing_mypy.py`,
  `tests/workflows/implement/test_task_processing_branch_name.py`,
  `tests/prompts/test_prompt_loader.py` (`test_existing_prompt_lookups_still_work`: drop
  the "Mypy Fix Prompt" case).

## WHAT

```python
_CHECK_OUTPUT_HEADING = "Check output:"

def _fix_check_text(project_dir: Path) -> str | None:
    """Raw `fix.check` fragment; None if missing, "" or prompt_fragments() raises."""

def _build_fix_prompt(
    fix_check: str, fix_text: str, check_instructions: str
) -> str: ...
```

## HOW

- `_fix_check_text` calls `load_toolkit(project_dir).toolkit.prompt_fragments()` inside
  `try/except Exception` (logs the exception at warning level).
- Called **once**, after the initial `_run_check` reports findings (a clean run loads
  nothing extra).
- `check_instructions` for the prompt, computed once next to `fix_check`:
  - `bash_grants = bash_grants_of(llm_permissions(project_dir, provider))` (move the
    existing per-attempt computation up so it is shared);
  - if `bash_grants_of(llm_permissions(project_dir, "claude"))` (toolkit declares Bash
    grants): `resolve_prompt_slots("[check_instructions]", project_dir, provider,
    bash_grants).get("check_instructions", "")`; otherwise `""`.
- Remove the `get_prompt(... "Mypy Fix Prompt")` block and the `get_prompt` /
  `PROMPTS_FILE_PATH` imports if they become unused (the implementation template still
  uses them — keep if used).

## ALGORITHM

```
result = _run_check(...); if result is None: return True
fix_check = _fix_check_text(project_dir)
if not fix_check: logger.warning("No usable fix.check fragment ..."); return False
bash_grants = ...; check_instructions = ... (only for Bash-grant toolkits)
loop: prompt = _build_fix_prompt(fix_check, result, check_instructions); prompt_llm(...)
_build_fix_prompt: "\n\n".join(p for p in [fix_check, f"{HEADING}\n{fix_text}", check_instructions] if p)
```

## DATA

`check_and_fix_mypy` return contract unchanged (`True` clean / `False` otherwise; typed LLM
errors still propagate). Unusable `fix.check` → `False`.

## Docs

`05-implementation.md`:
- line ~39: "(pylint → pytest → mypy)" → neutral, e.g. "The LLM runs the project's quality
  checks after each step, as its prompt tells it to".
- line ~46: replace the `prompts.md#mypy-fix-prompt` link with plain text: "the toolkit's
  `fix.check` fragment (`prompt_fragments()`)".

## Tests

- Clean initial check → `load_toolkit` called only by `_run_check` (patch
  `_fix_check_text` and assert not called).
- Findings + `fix.check` present → prompt = `fix.check`, blank line, `Check output:`, fix
  text; no `[mypy_output]`.
- `fix.check` missing / `""` / `prompt_fragments()` raises → warning logged, returns
  `False`, `prompt_llm` not called.
- Toolkit with Bash grants (Claude, grants given) → prompt ends with the filled
  `check_instructions`.
- Toolkit without Bash grants (Python-style) → no `check_instructions` appended.
- Update `[mypy_output]` mocks in `test_task_processing_mypy.py` and
  `test_task_processing_branch_name.py` to the new fragment-based setup.
- `prompts.md` no longer has a "Mypy Fix Prompt" header.
