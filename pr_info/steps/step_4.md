# Step 4: Prompts for restructure and feedback; planner line

See `pr_info/steps/summary.md` (§3 prompt text, §7 of issue #1093).

## WHERE
- `src/mcp_coder/prompts/prompts.md`
- Tests: `tests/prompts/test_prompt_loader.py`

## WHAT
Two new prompt sections under "Prompts for task tracker based workflows", after
"Task Tracker Update Prompt", each a `###` group header + `####` prompt header + code block
(like "Mypy Fix Prompt"):
- `#### Task Tracker Restructure Prompt`, placeholders `[violations]`, `[expected_format]`.
  Content: fix the structure of `pr_info/TASK_TRACKER.md` only; checkbox lines may be moved
  but never deleted, reworded, checked or unchecked; no new checkbox under a step that has a
  checked box; headers, blank lines and comments may be added, edited, moved or removed; edit
  no other file.
- `#### Task Tracker Feedback Prompt`, placeholders `[violations]`, `[expected_format]`.
  Content: the tracker is still invalid, here are the problems and the expected structure;
  fix `pr_info/TASK_TRACKER.md` only; do not check or uncheck checkboxes.

Planner: in "Implementation Plan Creation", add to the `### Requirements:` list:
`- Do not edit \`pr_info/TASK_TRACKER.md\` — the implement workflow populates it from the step files.`

## HOW
No line of the new prompt bodies may start with `#` after stripping, even inside the code
fence: `prompt_parsing._extract_headers` treats it as a header and duplicates break every
lookup. Refer to sections inline, e.g. "the `## Tasks` section" mid-sentence. The expected
skeleton (which contains `###` lines) comes in only through `[expected_format]`.
Placeholders are filled with `str.replace`, as `task_processing` does for `[mypy_output]`.

## ALGORITHM
None.

## DATA
Prompt strings via `get_prompt(str(PROMPTS_FILE_PATH), "<name>")`.

## Tests (write first)
- `get_prompt` returns both new prompts; each contains `[violations]` and `[expected_format]`;
  no line in either starts with `#` after `strip()`.
- Existing lookups still work: "Task Tracker Update Prompt", "Mypy Fix Prompt", "Implementation Plan Creation".
- "Implementation Plan Creation" contains "Do not edit `pr_info/TASK_TRACKER.md`".

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement step 4 only:
> write the prompt-loader tests first, then add the two prompt sections and the planner
> requirement line to `prompts.md`. No line of the new prompt bodies may start with `#`.
> Run pylint, pytest (`-n auto`, unit markers) and mypy.
