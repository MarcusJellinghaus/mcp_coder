# Step 6 — Remove the fabricate pressure: `RETRY_REMINDER` + `prompts.md`

The mechanism now exists; this step tells the agent about it and stops pushing it through
the wrong door.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/task_processing.py` | replace `RETRY_REMINDER` (`:39`) |
| `src/mcp_coder/prompts/prompts.md` | condition the rule at `:115`, add one bullet |
| `tests/workflows/implement/test_task_processing.py` | two content assertions |

## WHAT

`RETRY_REMINDER` — a **replacement**, verbatim:

```python
RETRY_REMINDER = (
    "\n\n⚠️ Previous attempt produced NO file changes. "
    "If the task is already complete AND you saw its checks pass, tick the "
    "checkbox [ ] → [x] in pr_info/TASK_TRACKER.md — that file edit IS the "
    "deliverable. If the task genuinely needs code, do the work now. "
    "If something blocks you from either, write one line to "
    "pr_info/.blocked.txt saying what, and stop."
)
```

`prompts.md:115` — replace the existing single bullet with these two, in place:

```
- If a sub-task is already complete and you saw its checks pass, STILL tick the box `[ ]` → `[x]`. Ticking the checkbox IS the required deliverable for that sub-task.
- If something blocks you from verifying a sub-task, write one line to `pr_info/.blocked.txt` saying what blocked you, and stop. Do not tick a check you did not see pass.
```

## HOW

- **Replace, do not append.** Appending the blocked exit to the existing `RETRY_REMINDER`
  would leave *"If the task is already complete, you MUST tick … IS the deliverable"*
  standing two sentences away. An agent under retry pressure resolves that contradiction
  toward the stronger imperative — which is exactly the observed run 2 behaviour.
- Same reasoning for `prompts.md:115`: **condition the bullet itself**, do not add a
  qualifying bullet after it. The rule still earns its place (it stops the agent doing
  nothing when a task is genuinely done); it just needs the precondition.
- `prompts.md:115` governs attempt 1, before any retry reminder exists — both edits are
  required, neither is redundant.
- Retry count stays at 3 (`MAX_NO_CHANGE_RETRIES`); attempts 2 and 3 remain identical to
  each other. No change to the retry mechanics.

## ALGORITHM

None — prompt text only.

## DATA

Three exits offered, no sentence contradicting its neighbour: tick (conditioned on having
seen the checks pass) / do the work / write `.blocked.txt` and stop.

## TESTS (write first)

No existing test asserts `RETRY_REMINDER`'s content — `test_task_processing.py:507,534` use
the imported symbol, not a literal — so both remain valid unchanged. Add two cheap
assertions that pin the constant-to-prompt link:

1. `test_retry_reminder_offers_blocked_exit` — `BLOCKED_FILE in RETRY_REMINDER`
   (`BLOCKED_FILE` is `"pr_info/.blocked.txt"`, which the text contains verbatim). Assert
   the reminder no longer contains the unconditional `"you MUST tick"` phrasing.
2. `test_implementation_prompt_offers_blocked_exit` — load the
   `"Implementation Prompt Template using task tracker"` section via `get_prompt` with
   `PROMPTS_FILE_PATH` (as `process_single_task` does) and assert `BLOCKED_FILE` appears in
   it.

Both go in `tests/workflows/implement/test_task_processing.py` — keeping them there avoids
a new test module and keeps the constant and the prompt asserted together.

## COMMIT

`Offer a blocked exit in the retry reminder and base prompt`

## LLM PROMPT

```
Read pr_info/steps/summary.md (section 7) and pr_info/steps/step_6.md, then implement
Step 6 only.

Two text edits: replace RETRY_REMINDER in task_processing.py, and condition the rule at
prompts.md line 115 in place while adding one new bullet after it. Use the exact wording
given in the step file.

The critical instruction: RETRY_REMINDER is REPLACED wholesale, not extended, and the
prompts.md bullet is CONDITIONED IN PLACE, not followed by a qualifier. Leaving the old
unconditional "ticking the checkbox IS the deliverable" sentence standing anywhere in
either text reproduces the exact failure this issue documents — an agent under retry
pressure resolves the contradiction toward the stronger imperative and fabricates a
passing check.

Do not change MAX_NO_CHANGE_RETRIES or any retry mechanics.

Work test-first: add the two content assertions described in the step file to
tests/workflows/implement/test_task_processing.py, watch them fail, then edit the text.

Use MCP tools for all file operations. When done, run all three checks and fix everything
they report:
  mcp__tools-py__run_pylint_check
  mcp__tools-py__run_mypy_check
  mcp__tools-py__run_pytest_check with
    extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and
    not claude_api_integration and not formatter_integration and not github_integration
    and not langchain_integration"]

Then run ./tools/format_all.sh and make exactly one commit.
```
