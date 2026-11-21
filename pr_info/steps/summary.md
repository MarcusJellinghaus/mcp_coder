# Summary: create-pr uses the compact diff for PR summary and description refresh (#106)

## Goal

The PR-summary prompt (create-pr) and the PR-description-refresh prompt (create-pr post-creation, fix-ci) get the **compact diff** (`get_compact_diff`) instead of the full branch diff (`get_branch_diff`). The compact diff keeps a short preview of each block that moved unchanged and collapses the rest of the block into one marker line, so refactors and file splits cost fewer tokens.

## Architectural / design changes

- **One shared diff source for PR text.** The new helper `get_pr_diff(project_dir, base_branch) -> str` in `src/mcp_coder/workflow_steps/pr_description.py` is the only place that builds the diff for the PR prompts:
  - It calls `get_compact_diff(project_dir, base_branch, exclude_paths=["pr_info/"])`.
  - If that raises, it logs a warning and falls back to `get_branch_diff(project_dir, base_branch=base_branch, exclude_paths=["pr_info/"])`.
  - It owns the `pr_info/` exclusion that used to be duplicated at both call sites.
  - Both call sites use it, so creation and refresh always see the same input. The refresh prompt compares the current body against the diff, so this matters.
- **Fall back, don't fail.** Inside `get_compact_diff` only `render_compact_diff` can raise (`get_branch_diff` catches everything and returns `""`). Without the fallback, a renderer bug (MarcusJellinghaus/mcp-workspace#406, an `IndexError` on a form-feed-only line) would abort create-pr with `status-09f`.
- **Empty diff → unchanged behaviour.** Each caller keeps its own empty-diff check. create-pr then falls back to the title "Pull Request", and refresh skips.
- **Layering.** The helper lives in `workflow_steps`, one layer below `workflows`. `workflows/create_pr/core.py` imports it directly from `mcp_coder.workflow_steps.pr_description`, an import edge that already exists via `create_pr/helpers.py` and `post_creation.py`. There is no re-export, and the import-linter and tach configs stay unchanged. `get_compact_diff` is imported through the `mcp_coder.mcp_workspace_git` shim.
- **Prompts explain the move markers.** Both prompts get one sentence about the markers `# [moved from <file>: N lines not shown]`, `# [moved to <file>: N lines not shown]` and `# [moved: N lines not shown]`:
  - A marker that names another file → describe the block as a move.
  - A marker that names the same file → the block was re-indented or reordered in place.
  - Never describe a marked block as an addition or removal.
- **Side effect, intended.** fix-ci calls `refresh_pr_description`, so its refresh input also becomes the compact diff.
- **Out of scope.** Handling diffs too large for the context is #383. That logic will go into `get_pr_diff` later.

## Files modified

| File | Change |
|---|---|
| `src/mcp_coder/workflow_steps/pr_description.py` | add `get_pr_diff`; `refresh_pr_description` uses it; docstring update |
| `src/mcp_coder/workflows/create_pr/core.py` | `generate_pr_summary` uses `get_pr_diff`; drop the `get_branch_diff` import (the file gets shorter; it has to stay under the 750-line limit) |
| `src/mcp_coder/prompts/prompts.md` | marker sentence in `PR Summary Generation` and `PR Description Refresh`; "full git diff" → "branch diff" |
| `src/mcp_coder/workflows/implement/finalisation.py` | drop the stale diff clause from a comment |
| `tests/workflow_steps/test_pr_description.py` | the fixture patches `get_pr_diff`; helper tests; prompt-marker test |
| `tests/workflows/create_pr/test_generation.py` | patch `get_pr_diff` instead of `get_branch_diff`; remove the git-diff-exception test |
| `docs/processes-prompts/processes/08-pr-creation.md` | compact diff for create and refresh; fix the stale cleanup bullet; link the refresh prompt |
| `docs/cli-reference.md` | "full branch diff" → "compact branch diff" |

No files are created or deleted outside `pr_info/`. Not touched: `tests/workflows/test_create_pr_integration.py` (prompts are resolved from the package; `test_pr_summary_generation_with_diff` runs the real compact diff and must still pass), and the fix-ci / post-creation tests (they patch `refresh_pr_description` as a whole).

## Steps

1. `get_pr_diff` helper + `refresh_pr_description` switched to it (tests first).
2. `generate_pr_summary` in create-pr switched to `get_pr_diff` (tests first).
3. Prompt sentence about move markers in both prompts (test first).
4. Docs and stale comment (text only).
