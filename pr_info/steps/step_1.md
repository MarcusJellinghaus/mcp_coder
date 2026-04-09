# Step 1: Move FINALISATION_PROMPT to prompts.md

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #310

## WHERE

- `src/mcp_coder/prompts/prompts.md` — add new prompt section
- `src/mcp_coder/workflows/implement/core.py` — remove constant, update `run_finalisation`

## WHAT

Move the `FINALISATION_PROMPT` f-string constant (lines 84-100 of core.py) into `prompts.md` as a new prompt under the header `Finalisation Prompt`. Update `run_finalisation` to load it via `get_prompt_with_substitutions`.

## HOW

### 1. Add to prompts.md

Append a new section under `## Prompts for task tracker based workflows` (before `## Plan Generation Workflow`), with header `#### Finalisation Prompt` and a code block containing the prompt text. Replace the Python f-string interpolation values with `[placeholder]` syntax:

- `{PR_INFO_DIR}` → `[pr_info_dir]` (appears 3 times)
- `{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}` → `[commit_message_path]` (appears once on the last line)

The rendered text must be **identical** to what the f-string produced:
- `PR_INFO_DIR` = `"pr_info"`
- `COMMIT_MESSAGE_FILE` = `"pr_info/.commit_message.txt"`
- So `{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}` rendered to `pr_info/pr_info/.commit_message.txt`

Prompt text for the code block:
```
Please check [pr_info_dir]/TASK_TRACKER.md for unchecked tasks (- [ ]).

For each unchecked task:
1. If it's a "commit message" task and changes are already committed → mark [x] and skip
2. Otherwise: verify if done, complete it if not, then mark [x]

If step files exist in [pr_info_dir]/steps/, use them for context.
If not, analyse based on task names and codebase.

If you cannot complete a task, DO NOT mark the box as done.
Instead, briefly explain the issue.

Run quality checks (pylint, pytest, mypy) if any code changes were made.
Write commit message to [commit_message_path].
```

### 2. Update run_finalisation in core.py

Replace line 933 (`FINALISATION_PROMPT` usage) with:

```python
finalisation_prompt = get_prompt_with_substitutions(
    str(PROMPTS_FILE_PATH),
    "Finalisation Prompt",
    {
        "pr_info_dir": PR_INFO_DIR,
        "commit_message_path": f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}",
    },
)
```

Then use `finalisation_prompt` in both the `prompt_llm` call (line 932-940) and the `store_session` call (line 943-951) where `FINALISATION_PROMPT` was previously referenced.

### 3. Delete the FINALISATION_PROMPT constant

Remove lines 84-100 (the constant and its comment).

### 4. Clean up imports

`get_prompt_with_substitutions` is already imported in core.py (line 21). `PROMPTS_FILE_PATH` is already imported (line 17). No import changes needed.

## DATA

- `get_prompt_with_substitutions` returns `str` — same type as the old constant
- No signature changes to any function

## ALGORITHM

```
1. Load prompt from prompts.md with placeholder substitutions
2. Pass loaded string to prompt_llm (replacing constant reference)
3. Pass loaded string to store_session (replacing constant reference)
```

## Tests

Existing `TestRunFinalisation` tests in `test_core.py` should continue to pass. The test at line 828-830 asserts `"TASK_TRACKER.md" in prompt` — this still holds since the loaded prompt contains that text.

No new tests needed — this is a mechanical move with no logic change.

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md (see also pr_info/steps/summary.md).

Move the FINALISATION_PROMPT constant from core.py to prompts.md and update run_finalisation to load it via get_prompt_with_substitutions. No logic changes — only location and loading mechanism change.

After changes: run pylint, pytest, mypy and fix any issues.
Write commit message to pr_info/.commit_message.txt.
```
