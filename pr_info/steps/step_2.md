# Step 2 — Workflow prompts: neutral wording + slots, filled by their callers

See `pr_info/steps/summary.md` ("Where slots are filled"). Requires Step 1.

## LLM prompt

> Implement Step 2 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_2.md`.
> Update the tests first, then change `prompts.md` and the four callers in the same commit
> (a slot without a filling caller would leak a literal `[check_instructions]`).
> Do not touch the Mypy Fix Prompt or the Rebase sections (Steps 4 and 5).
> Run pylint, mypy and pytest; all must pass.

## WHERE

- `src/mcp_coder/prompts/prompts.md`
- `src/mcp_coder/workflow_steps/ci.py` (`_run_ci_fix`)
- `src/mcp_coder/workflows/implement/finalisation.py` (`run_finalisation`)
- `src/mcp_coder/workflows/implement/task_processing.py` (`process_single_task`)
- `src/mcp_coder/workflows/create_plan/core.py` (`_load_prompt_or_exit` callers)
- `docs/repository-setup/claude-code.md`
- Tests: `tests/workflow_steps/test_ci.py`, `tests/workflow_steps/test_ci_bash_grants.py`,
  finalisation / task-processing tests in `tests/workflows/implement/`, create_plan tests.

## WHAT — prompt text (`prompts.md`)

| Section | Change |
|---|---|
| Task Tracker Update Prompt | `- Quality checks: pylint, pytest, mypy — fix all issues` → `- Quality checks — fix all issues` (no slot) |
| Implementation Prompt Template | Bullet → `- Run the project's quality checks when required`; after the last bullet of `**2. FOR EACH SUB-TASK**` add a blank line then `[check_instructions]` on its own line, before `**3. COMPLETE THE STEP**` |
| Implementation Prompt Template RULES | `- Use MCP tools for all operations` → `- Use MCP tools for file and git operations` |
| Finalisation Prompt | `Run quality checks (pylint, pytest, mypy) if any code changes were made.` → `Run the project's quality checks if any code changes were made.` followed by `[check_instructions]` on its own line, then the commit-message line |
| Implementation Plan Creation | `## Python Project Implementation Plan Request` → `## Implementation Plan Request`, followed by `[language_context]` on its own line |
| Review Implementation Reviewer | `Python conventions` → `language conventions` |
| CI Fix Prompt | Step 3 → `3. Run the project's quality checks — all of them, not just the one that failed`; add a blank line and `[check_instructions]` on its own line after step 6, before `**Rules:**`. "Repeat step 3-4" stays valid. |

## WHAT — callers

Each caller: `template = get_prompt(...)`, compute `bash_grants` **before** building the
prompt, then:

```python
prompt = fill_prompt(
    template, substitutions,
    resolve_prompt_slots(template, project_dir, provider, bash_grants),
)
```

- `_run_ci_fix`: move the `bash_grants = bash_grants_of(llm_permissions(...))` line above the
  prompt build; substitutions `{"problem_description": problem_description}`; keep the
  existing `try/except` → `return False` around prompt loading. The CI analysis prompt keeps
  `get_prompt_with_substitutions`.
- `run_finalisation`: move `bash_grants` above; substitutions as today
  (`pr_info_dir`, `commit_message_path`).
- `process_single_task`: compute `bash_grants` before loading the template; fill the
  template with `{}` substitutions **before** the f-string appends the task line.
- `create_plan` (`run_planning_prompts`, after `prompt_3 = _load_prompt_or_exit(...)`):
  `prompt_3 = fill_prompt(prompt_3, {}, resolve_prompt_slots(prompt_3, project_dir, provider, None))`.
  Only the plan request has a slot. `bash_grants=None` because create_plan's
  `prompt_llm` calls pass no grants (the plan request only uses `[language_context]`).

## HOW

- Import `from mcp_coder.utils.prompt_slots import fill_prompt, resolve_prompt_slots`.
- `ci.py`: replace the `get_prompt_with_substitutions` import use in `_run_ci_fix` with
  `get_prompt` + the two functions (analysis prompt unchanged).

## ALGORITHM

None beyond the three-line pattern above.

## DATA

Unchanged return types of all callers.

## Docs

`docs/repository-setup/claude-code.md` line ~21: replace "`implement` assumes Claude can
read files and run pylint, pytest and mypy, preferably through these MCP tools." with a
neutral sentence: `implement` assumes Claude can read files and run the checks of the
configured toolkit (for Python projects, the `mcp-tools-py` MCP tools).

## Tests

- `test_ci.py` / `test_ci_bash_grants.py`: patch `ci.get_prompt` /
  `ci.resolve_prompt_slots` instead of `ci.get_prompt_with_substitutions`; assert the
  prompt passed to `prompt_llm` contains the problem description and the slot value;
  assert `resolve_prompt_slots` receives the same `bash_grants` passed to `prompt_llm`.
- Finalisation: the prompt contains the `check_instructions` value; with `""` the slot line
  is gone and `[pr_info_dir]` is substituted.
- Task processing: the template is filled before the task line; a task name containing
  `[check_instructions]` is not filled.
- create_plan: plan-request prompt has `[language_context]` filled (or its line removed for
  `""`).
- Prompt-text test (in `tests/prompts/test_prompt_loader.py` or a new test there): the
  Implementation, Finalisation, CI Fix and plan prompts contain their slot on a line of its
  own, and none of these sections contains `pylint`, `mypy`, `pytest` or (case-insensitive)
  `python project`.
