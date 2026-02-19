# Summary: feat #469 — Compact Diff for Large/Refactoring Branches

## Problem

`git diff` for refactoring branches (e.g. splitting one large file into multiple
modules) produces massive output: the entire original file appears as deleted, all
new files appear as added, even when no logic changed. This makes the diff too
large for LLM review.

Two standalone prototype tools (`tools/compact_diff.py`,
`tools/git-refactor-diff.py`) solved this with 35–74% reduction but have
overlapping functionality and are not integrated into the CLI.

---

## Solution Overview

A sequential two-pass pipeline that detects "moved" code blocks (code that
appears verbatim in another file) and replaces them with compact summary
comments, reducing diff size dramatically while preserving all real changes.

**Pass 1 (ANSI):** Run `git diff --color=always --color-moved=dimmed-zebra` and
parse ANSI escape codes to identify which lines git classifies as moved
(≥20 alphanumeric character threshold).

**Pass 2 (Python):** Collect all removed/added lines across files; find their
intersection (lines present as both a removal and an addition = moved). Suppress
consecutive moved blocks of ≥3 lines / ≥10 char content.

Moved blocks are **not silently dropped**; they emit a summary comment:
```
# [moved: N lines not shown]
```

---

## Architectural / Design Changes

### New module
`src/mcp_coder/utils/git_operations/compact_diffs.py`

Pure functions organized in five layers (parsing → ANSI → Python matching →
block analysis → rendering). Each layer is independently unit-testable with
synthetic data only (no large fixture files).

### Extended function
`get_branch_diff()` in `src/mcp_coder/utils/git_operations/diffs.py` gains an
optional `ansi: bool = False` parameter. When `True`, adds `--color=always` to
the diff args. Backward-compatible (default unchanged).

### New CLI command group
`mcp-coder git-tool compact-diff` — parallel to the existing `gh-tool` group.
Wired via:
- `src/mcp_coder/cli/commands/git_tool.py` (new)
- `src/mcp_coder/cli/parsers.py` — new `add_git_tool_parsers()` function
- `src/mcp_coder/cli/main.py` — new `_handle_git_tool_command()` and routing

### Updated slash command
`.claude/commands/implementation_review.md` replaces the raw `git diff` call
with `mcp-coder git-tool compact-diff`.

### Deleted prototype tools
`tools/git-refactor-diff.py` and `tools/compact_diff.py` are removed (superseded).

---

## Files Created or Modified

| Action   | File |
|----------|------|
| **Create** | `src/mcp_coder/utils/git_operations/compact_diffs.py` |
| **Create** | `src/mcp_coder/cli/commands/git_tool.py` |
| **Create** | `tests/utils/git_operations/test_compact_diffs.py` |
| **Create** | `tests/cli/commands/test_git_tool.py` |
| **Modify** | `src/mcp_coder/utils/git_operations/diffs.py` — add `ansi` param |
| **Modify** | `src/mcp_coder/cli/parsers.py` — add `add_git_tool_parsers()` |
| **Modify** | `src/mcp_coder/cli/main.py` — wire `git-tool` command routing |
| **Modify** | `.claude/commands/implementation_review.md` — replace `git diff` with CLI call |
| **Delete** | `tools/git-refactor-diff.py` |
| **Delete** | `tools/compact_diff.py` |

---

## KISS Simplifications vs Original Prototype Tools

- **No cross-file source→dest line range tracking.** The exact
  `# [moved: src/foo.py:123–167 → dst/bar.py:45–89]` format from the issue
  description requires complex bookkeeping that is fragile for edge cases
  (lines present in 3+ files). Replaced with the simpler in-hunk
  `# [moved: N lines not shown]` summary that still satisfies the "not silently
  dropped" requirement.
- **No clipboard or `--stat` mode.** Those were prototype-tool ergonomics, not
  required by the issue.
- **No `__init__.py` re-export.** `compact_diffs.py` is internal to the CLI
  command; no public API surface needed.
- **Single-file module.** `compact_diffs.py` stays one file (well under 600-line
  threshold); no subpackage needed.

---

## Implementation Steps

| Step | Title |
|------|-------|
| 1 | Extend `get_branch_diff()` with `ansi` parameter + tests |
| 2 | Create `compact_diffs.py` core module + unit tests |
| 3 | Create `git_tool.py` CLI command + parser + main.py wiring + tests |
| 4 | Update `implementation_review.md` + delete prototype tools |
