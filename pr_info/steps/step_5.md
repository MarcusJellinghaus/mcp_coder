# Step 5 — Prompt wording: prose is not a report

See [summary.md](./summary.md). Independent of Steps 1–4. Fixes the cause at the source: the
blocked channel works, but it lost to a generated step instruction saying "stop and **report**",
which the agent satisfied by writing prose into the step file — a file change, which the old gate
read as success.

## WHERE

- `src/mcp_coder/prompts/prompts.md` — two sections:
  - Implementation Prompt Template using task tracker (RULES block, `:111-116`)
  - Implementation Plan Creation (`:225-245`)
- `tests/workflows/implement/test_task_processing.py` — `TestBlockedExitInPrompts` (`:195-222`)

## WHAT

No Python source changes. Two prompt edits: one reword, one addition.

## HOW

- Prompts are read by `get_prompt(str(PROMPTS_FILE_PATH), "<section heading>")`. The headings and
  the fenced code blocks must keep their current structure — `get_prompt` locates sections by
  heading, and the existing tests load these two by name.
- The Implementation Plan Creation section currently contains **no** precondition wording at all,
  so that part is new text, not a rewrite. The "stop and report" phrasing this fixes came from
  generated output (`pr_info/steps/step_2.md` in #1146), which is exactly what this prompt
  controls.

## ALGORITHM

**Edit 1 — reword the RULES bullet at `:116`**, keeping `pr_info/.blocked.txt` in the text (an
existing test asserts the constant appears in the template):

```
- If something blocks you from verifying or completing a sub-task, write one line to
  `pr_info/.blocked.txt` saying what blocked you, and stop. That file is the ONLY way to report a
  problem. Writing notes, explanations or status paragraphs into a step file, a plan file or the
  task tracker is NOT a report and does NOT count as progress. Do not tick a check you did not see
  pass.
```

**Edit 2 — add to the Implementation Plan Creation requirements** (inside the existing fenced
block, under `### Requirements:`):

```
- If a step has a precondition that may not hold, phrase the failure action as "write one line to
  `pr_info/.blocked.txt` and stop" — never "stop and report", and never "document the problem".
  Prose in a step or plan file is not a report and the workflow cannot see it.
```

## DATA

No runtime data structures. Rendered prompt text only; both sections keep their current headings
so `get_prompt` resolves them unchanged.

## Tests (write first)

Extend `TestBlockedExitInPrompts` in `test_task_processing.py`:

1. The implementation template contains the word `ONLY` (or equivalent exclusivity wording) in the
   same bullet as `pr_info/.blocked.txt` — the reword is load-bearing, not cosmetic.
2. The implementation template does not contain the phrase `stop and report`.
3. `get_prompt(..., "Implementation Plan Creation")` contains `pr_info/.blocked.txt` — today it
   contains no blocked wording at all, so this test fails before the edit.
4. The Implementation Plan Creation section does not contain `stop and report`.

The three existing assertions in that class must keep passing: `BLOCKED_FILE in prompt_template`,
`"you MUST tick" not in RETRY_REMINDER`, and the "before finishing" gate line still containing
`unless something blocks you`.

## Checks

`run_format_code`, then pylint / pytest / mypy.

## LLM prompt

> Implement Step 5 of `pr_info/steps/step_5.md`, with `pr_info/steps/summary.md` for context.
> Write the tests first, then the edits.
> In `src/mcp_coder/prompts/prompts.md`: reword the blocked-exit bullet in the RULES block of
> "Implementation Prompt Template using task tracker" so it states that `pr_info/.blocked.txt` is
> the only report channel and that prose in a step file, plan file or the task tracker is neither a
> report nor progress. Then add a new requirement to "Implementation Plan Creation" saying that any
> precondition in a generated step must be phrased "write one line to `pr_info/.blocked.txt` and
> stop", never "stop and report".
> Keep both section headings and their fenced code blocks intact — `get_prompt` resolves sections by
> heading. No Python source changes in this step.
> Run `run_format_code`, then pylint, pytest and mypy; fix everything before finishing.
