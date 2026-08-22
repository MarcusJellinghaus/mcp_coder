# Step 7 — `finalisation.py`: marker cleanup + the `commit_message_path` double prefix

Two small changes in one file: the third commit path gets cleanup, and a live behavioural
bug gets fixed while we are in there.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/finalisation.py` | cleanup in a `finally` on the LLM call (`:80-90`), path fix (`:76`) |
| `tests/workflows/implement/test_finalisation.py` | three tests |

## WHAT

### A. Marker cleanup in a `finally` on the finalisation LLM call

Same pattern as Step 3: the marker is cleared on **every** exit path, not just the happy one.

```python
try:
    llm_response = prompt_llm(
        finalisation_prompt,
        ...
    )
finally:
    read_and_clear_blocked(project_dir)   # never let a marker reach a commit
```

Imported from `.task_processing`; the return value is discarded.

### B. The double-prefix fix

```python
# before — resolves to pr_info/pr_info/.commit_message.txt
"commit_message_path": f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}",
# after
"commit_message_path": COMMIT_MESSAGE_FILE,
```

## HOW

**Placement of the cleanup matters, and a bare call in the happy path is not enough.**
Three constraints, all satisfied by one `finally` on the `prompt_llm` call:

- It must run **after** the LLM turn. Placed *before* the call it would only clear *stale*
  markers; one written by the finalisation agent itself would still be staged by
  `commit_all_changes`, which stages everything — and `create_pr/core.py`'s
  `get_branch_diff` excludes only `pr_info/steps/`, so a committed marker surfaces in the
  PR summary diff.
- It must run **before** the step-4 changes check at `:111`, or the marker reads as a
  change to commit.
- It must run on the **early exits too**. A bare call sitting just above `:111` is bypassed
  by the empty-response guard at `:104-106`, which returns `False`, and by anything
  `prompt_llm` raises. A marker left there is never cleared, and — exactly as in Step 3 —
  it poisons the next run: `check_git_clean` refuses it, and `prepare_task_tracker`
  hard-fails with `task_tracker_prep_failed` because it requires exactly one changed file
  equal to `TASK_TRACKER.md`.

The `finally` is attached to the `prompt_llm` call only, not to the rest of the function —
wrapping the whole body would put the cleanup *after* `commit_all_changes`, which is too
late.

**Cleanup only.** `run_finalisation` gets no blocked channel — it is a separate LLM turn
after the loop, and the decision is that a blocked finalisation is not a distinct outcome.

The early return at `:58-60` (`has_incomplete_work` false) returns before the LLM call ever
happens, so no marker can be written on that path; a *stale* one survives it untouched.
Accepted: `check_git_clean` gates the next run.

**Why B is not cosmetic.** `COMMIT_MESSAGE_FILE` is `"pr_info/.commit_message.txt"` — it
already carries the prefix. The placeholder **is** consumed (`prompts.md:196`: *"Write
commit message to [commit_message_path]."*), so today the finalisation agent is handed
`pr_info/pr_info/.commit_message.txt`, the Level-1 read at `:121` never finds the file, and
**every finalisation silently falls through to Level-2 LLM message generation**. Fixing it
restores the intended 3-level fallback.

## ALGORITHM

```
...existing step 1 (incomplete-work check)...
try:    llm_response = prompt_llm(...)      # existing call
finally: read_and_clear_blocked(project_dir)  # <- new; runs on every exit path
...existing store_session + empty-response guard (returns False -> marker already cleared)...
status = get_full_status(project_dir)
if nothing staged/modified/untracked: return True
...existing commit-message fallback + commit + push...
```

## DATA

No new types. `read_and_clear_blocked`'s return value is deliberately discarded here.

## TESTS (write first)

In `tests/workflows/implement/test_finalisation.py`, following the module's existing mock
setup:

1. `test_blocked_marker_removed_before_commit` — with `has_incomplete_work` true, a
   successful LLM response, a real marker file written under `tmp_path`, and
   `get_full_status` reporting a modified file: assert the marker no longer exists **and**
   `commit_all_changes` was called. (Cleanup happens, finalisation still proceeds.)
2. `test_blocked_marker_removed_on_empty_response` — same setup but `prompt_llm` returns an
   empty `text`: `run_finalisation` returns `False` **and** the marker is gone. This is the
   test that pins the `finally`; a bare call above the changes check fails it.
3. `test_commit_message_path_has_no_double_prefix` — capture the prompt passed to
   `prompt_llm` (or assert on the substitutions handed to
   `get_prompt_with_substitutions`) and assert it contains
   `"pr_info/.commit_message.txt"` and **not** `"pr_info/pr_info"`.

## COMMIT

`Clean blocked marker in finalisation and fix commit message path`

## LLM PROMPT

```
Read pr_info/steps/summary.md (sections 5 and 9) and pr_info/steps/step_7.md, then
implement Step 7 only.

Two changes in src/mcp_coder/workflows/implement/finalisation.py:
A. Wrap the existing prompt_llm call in try/finally and call
   read_and_clear_blocked(project_dir) in the finally.
B. Fix the commit_message_path substitution, which currently double-prefixes to
   pr_info/pr_info/.commit_message.txt.

Placement of A is the point of the change, and the finally is not decoration:
- Before the LLM call it would only clear stale markers, and one written by the
  finalisation agent itself would still be committed into the branch and surface in the PR
  summary diff.
- A bare call sitting just above the step-4 changes check is bypassed by the
  empty-response guard (finalisation.py:104-106 returns False) and by anything prompt_llm
  raises, leaving the marker on disk to poison the next run at check_git_clean.
- Do NOT wrap the whole function body in the try — that would run the cleanup after
  commit_all_changes, which is too late.
This is the same pattern Step 3 uses in process_single_task, for the same reason.

B is a live behavioural bug, not a typo — the placeholder is consumed by the finalisation
prompt, so today every finalisation loses its prepared commit message and silently falls
back to LLM generation. Expect existing tests around the commit-message fallback to change
behaviour; if one starts failing because Level 1 now works, that is the fix landing —
update the test to assert the correct behaviour and say so in the commit message.

run_finalisation gets cleanup only. Do not add a blocked outcome there.

Work test-first: write the two tests described in the step file, watch them fail, then
implement.

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
