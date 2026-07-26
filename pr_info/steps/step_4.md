# Step 4 — New prompts + permission pruning

Add the two new prompt sections and prune the dead `Bash(...)` grants. The old
"Automated Rebase" prompt section is **kept in this step** — its consumer
(`_run_rebase_session`) still exists until Step 6, and deleting both together keeps
every intermediate commit consistent. See [summary.md](./summary.md) ("Prompts",
"Permissions").

## WHERE

- Modify: `src/mcp_coder/prompts/prompts.md` (add two `##` sections after
  "Automated Rebase")
- Modify: `src/mcp_coder/workflows/rebase_permissions.py`
- Modify: `tests/workflows/rebase/test_prompt.py`
- Modify: `tests/workflows/rebase/test_rebase_permissions.py`

## WHAT — prompt sections

### `## Rebase Conflict Resolution`

Content requirements (fenced block, following the file's existing section format):

- Role: resolve the merge conflicts listed below during a rebase; a surrounding Python
  program runs all git commands — the LLM edits files only.
- Core philosophy from `/rebase`: base branch is source of truth; preserve its
  improvements, rework feature code to fit. Include the `/rebase` strategy table rows
  for code files / test files / config files (the `pr_info/` and lockfile rows are
  handled by Python and this repo has no lockfile — omit them).
- Placeholder `[conflict_context]`: Python replaces it with, per file: path plus the
  base (`:1:`), ours (`:2:`, base branch), theirs (`:3:`, feature branch) versions,
  with absent sides marked (delete/modify).
- Tools: edit via MCP file tools (`mcp__mcp-workspace__read_file`, `edit_file`,
  `save_file`, `delete_this_file`); read git state only via `mcp__mcp-workspace__git`.
- Explicit prohibitions: no shell commands, no staging/continuing/pushing (Python does
  all git writes), no outcome markers. Resolved files must contain no conflict markers.

### `## Rebase Regression Fix`

- Modeled on the existing "Mypy Fix Prompt" section (same placeholder pattern).
- Role: the rebase introduced the regressions below (new failures vs. the pre-rebase
  baseline); fix them via MCP file tools, preserving the intent of both branches.
- Placeholder `[regression_output]` for the concrete failure text.
- Same prohibitions: no shell, no git writes, no markers; reads via
  `mcp__mcp-workspace__git` only.

## WHAT — permissions

In `REBASE_LLM_PERMISSIONS`: delete **all ten** `Bash(...)` strings (including read-only
`git status`/`git diff` — the Bash tool does not exist in automated sessions). Keep
everything else exactly as-is (MCP file/check/format tools, `mcp__mcp-workspace__git`,
`get_base_branch`, the `enableAllProjectMcpServers`/`enabledMcpjsonServers` keys). Do
**not** add reference-project tools. Keep the EPIC #1038/#1054 TODO comment; update the
module docstring to explain that Bash grants are absent because non-interactive sessions
load no Bash tool (`--tools ToolSearch`).

## TDD

Update tests first:

1. `test_rebase_permissions.py`: replace assertions about `Bash(...)` entries with:
   no allow-entry starts with `"Bash("`; `mcp__mcp-workspace__git` and the MCP
   file/check tools are still present; no reference-project tools.
2. `test_prompt.py`: add tests that `get_prompt(PROMPTS_FILE_PATH, "Rebase Conflict
   Resolution")` and `... "Rebase Regression Fix")` load; each contains its placeholder
   (`[conflict_context]` / `[regression_output]`) and the string
   `mcp__mcp-workspace__git`; neither contains `REBASE_OUTCOME`, `git rebase`, or
   `Bash`. Existing "Automated Rebase" tests stay (section still exists until Step 6).

## DATA

No Python data structures; deliverables are markdown sections and a pruned dict.

## Commit

One commit. Suggested message:
`feat: add rebase conflict/regression prompts; prune dead Bash grants`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement `pr_info/steps/step_4.md`
> exactly: add the "Rebase Conflict Resolution" and "Rebase Regression Fix" sections to
> `src/mcp_coder/prompts/prompts.md` (keep the existing "Automated Rebase" section
> untouched — it is removed in Step 6), and remove every `Bash(...)` entry from
> `REBASE_LLM_PERMISSIONS` in `src/mcp_coder/workflows/rebase_permissions.py` without
> adding new grants. Update `tests/workflows/rebase/test_prompt.py` and
> `test_rebase_permissions.py` first (TDD). Run pylint, pytest, and mypy via the MCP
> check tools and fix any findings before finishing.
