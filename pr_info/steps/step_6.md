# Step 6 — Part 2: fallback commit message when LLM generation fails

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_6.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/workflow_steps/commit.py` ONLY. Do NOT touch `workflow_utils/commit_operations.py` or `cli/commands/commit.py` — the interactive `mcp-coder commit` must keep failing loudly.
- Tests: `tests/workflow_steps/test_commit.py`

## WHAT

Module constant:
```python
# Static fallback when LLM commit-message generation fails. Deliberately free
# of error detail: it lands in public git history; logs carry the diagnostics.
FALLBACK_COMMIT_MESSAGE = "chore: automated commit (message generation failed)"
```

In `commit_changes`, replace the early `return False` on generation failure with the fallback.

## ALGORITHM (changed block only)

```
if not commit_message:
    success, commit_message, error = generate_commit_message_with_llm(...)
    if not success:
        log error (as today)
        log "falling back to static commit message"
        commit_message = FALLBACK_COMMIT_MESSAGE      # was: return False
# flow continues into commit_all_changes(commit_message, project_dir) unchanged
```

Constraints (from the issue — do not deviate):
- **No special-casing of the "No changes to commit" error.** A clean tree flows through the fallback; `commit_all_changes` returns `success=True` on a clean tree, so `commit_changes` returns `True` without creating a commit. This is intentional and load-bearing for step 7.
- The broad `except` at the end of `commit_changes` keeps returning `False` (git itself failed; step 7 surfaces that).
- Skip the optional dedup of the 3-level fallback with `finalisation.py` (issue marks it non-blocking; KISS).

## DATA

- `commit_changes` return semantics: `True` = committed OR clean-tree no-op; `False` = git-level failure only (no longer "LLM failed").

## TESTS (write first)

In `tests/workflow_steps/test_commit.py` (existing mock patterns):
- Generation fails (`(False, "", "boom")`), dirty tree: `commit_all_changes` is called with `FALLBACK_COMMIT_MESSAGE`; `commit_changes` returns `True`.
- Generation fails with "No changes to commit", clean tree: `commit_all_changes` mocked to return `{"success": True, ...}` (no-op) → returns `True`.
- Generation succeeds: LLM message used, fallback NOT used (existing tests).
- `commit_all_changes` itself fails → still returns `False`.
- Prepared-message-file path unaffected.
- Verify no change to `generate_commit_message_with_llm` behavior (interactive failure path covered by existing `tests/cli/commands/test_commit.py` — must still pass unmodified).

## Commit

`fix: commit with static fallback message when LLM generation fails in workflow commit step (#1090)`
