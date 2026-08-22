# Step 7 — `finalisation.py`: marker cleanup + the `commit_message_path` double prefix

Two small changes in one file: the third commit path gets cleanup, and a live behavioural
bug gets fixed while we are in there.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflows/implement/finalisation.py` | cleanup call (`~:111`), path fix (`:76`) |
| `tests/workflows/implement/test_finalisation.py` | two tests |

## WHAT

### A. Marker cleanup before the step-4 changes check

```python
read_and_clear_blocked(project_dir)   # never let a marker reach a commit
status = get_full_status(project_dir)
if not status["staged"] and not status["modified"] and not status["untracked"]:
    ...
```

Imported from `.task_processing`.

### B. The double-prefix fix

```python
# before — resolves to pr_info/pr_info/.commit_message.txt
"commit_message_path": f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}",
# after
"commit_message_path": COMMIT_MESSAGE_FILE,
```

## HOW

**Placement of the cleanup matters.** It goes immediately before the step-4 changes check,
**not** before the LLM call at `:80-90`. Before the call it would only clear *stale*
markers; one written by the finalisation agent itself would still be staged by
`commit_all_changes`, which stages everything — and `create_pr/core.py`'s `get_branch_diff`
excludes only `pr_info/steps/`, so a committed marker surfaces in the PR summary diff.

**Cleanup only.** `run_finalisation` gets no blocked channel — it is a separate LLM turn
after the loop, and the decision is that a blocked finalisation is not a distinct outcome.

The early return at `:58-60` (`has_incomplete_work` false) skips the whole body, so a stale
marker survives that path untouched. Accepted: `check_git_clean` gates the next run.

**Why B is not cosmetic.** `COMMIT_MESSAGE_FILE` is `"pr_info/.commit_message.txt"` — it
already carries the prefix. The placeholder **is** consumed (`prompts.md:196`: *"Write
commit message to [commit_message_path]."*), so today the finalisation agent is handed
`pr_info/pr_info/.commit_message.txt`, the Level-1 read at `:121` never finds the file, and
**every finalisation silently falls through to Level-2 LLM message generation**. Fixing it
restores the intended 3-level fallback.

## ALGORITHM

```
...existing steps 1-3 (incomplete-work check, LLM turn, empty-response guard)...
read_and_clear_blocked(project_dir)          # <- new, immediately before the check below
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
2. `test_commit_message_path_has_no_double_prefix` — capture the prompt passed to
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
A. Call read_and_clear_blocked(project_dir) immediately before the step-4 changes check.
B. Fix the commit_message_path substitution, which currently double-prefixes to
   pr_info/pr_info/.commit_message.txt.

Placement of A is the point of the change: it must sit immediately before the changes
check, NOT before the LLM call. Placed before the call it would only clear stale markers,
and one written by the finalisation agent itself would still be committed into the branch
and surface in the PR summary diff.

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
