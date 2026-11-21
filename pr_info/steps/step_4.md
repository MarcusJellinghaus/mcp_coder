# Step 4: docs and stale comment

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` only (steps 1–3 are already done). This is a text-only step; no tests are needed. Keep the edits minimal and in the style of the surrounding text. Use the MCP tools for all file, check and git operations. When done, all checks listed below must pass. This step is exactly one commit.

## WHERE

- `docs/processes-prompts/processes/08-pr-creation.md`
- `docs/cli-reference.md`
- `src/mcp_coder/workflows/implement/finalisation.py` (comment only)

## WHAT / HOW

### `docs/processes-prompts/processes/08-pr-creation.md` (the **Process:** list)

- Replace the bullet `Generates PR summary from git diff using LLM (the diff excludes `pr_info/`)` with:
  `Generates PR summary using LLM from the compact branch diff: moved-but-unchanged blocks keep a short preview and collapse to a marker line; the diff excludes `pr_info/`. If the compact diff fails, the plain branch diff is used.`
- Replace the stale bullet `Cleans up pr_info folder (deletes steps/, clears TASK_TRACKER.md tasks)` with:
  `Deletes the `pr_info/` folder`
- In the refresh bullet (`If the rebase pushed new commits, refreshes the PR title/body ...`), state that the refresh uses the same compact diff, e.g. `refreshes the PR title/body from the same compact diff (best-effort, never changes the label); `fix-ci` does the same after pushing fixes`.
- Replace the prompt bullet with:
  `Uses prompts 🔗 [PR Summary Generation](../../../src/mcp_coder/prompts/prompts.md#pr-summary-generation) and 🔗 [PR Description Refresh](../../../src/mcp_coder/prompts/prompts.md#pr-description-refresh)`

### `docs/cli-reference.md` (around line 317)

- `regenerated from the full branch diff` → `regenerated from the compact branch diff`.

### `src/mcp_coder/workflows/implement/finalisation.py` (comment in the `finally:` block, about lines 97–101)

- Drop the stale clause `and create_pr's get_branch_diff excludes only pr_info/steps/`. Keep the rest of the comment and reflow it, e.g.:
  ```python
  # Never let a marker reach a commit: commit_all_changes stages everything.
  # Must run after the LLM turn (to catch a marker the agent just wrote),
  # before the changes check below, and on the early exits too. Return value
  # unused - run_finalisation has no blocked outcome.
  ```
- The code is unchanged.

## ALGORITHM / DATA

None.

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"]`
- `mcp__mcp-workspace__search_files` with pattern `full branch diff|full git diff`, glob `docs/**/*.md`: no matches. Run the same search with glob `src/mcp_coder/prompts/prompts.md`: no matches. (The `get_pr_diff` fallback mentions "full branch diff" on purpose, so `src/` as a whole is not checked.)

## Commit message

`docs(create-pr): document compact diff for PR summary and refresh`
