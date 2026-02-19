# Step 5: Update documentation

## Goal

Add concise documentation for the new `mcp-coder git-tool compact-diff` command
to the three relevant docs. No tests required for this step.

---

## WHERE

**Modify:** `docs/cli-reference.md`  
**Modify:** `docs/architecture/architecture.md`  
**Modify:** `README.md`

---

## WHAT

### `docs/cli-reference.md`

Add a `git-tool` section mirroring the existing `gh-tool` section style:

```
## git-tool

Git utility commands.

### git-tool compact-diff

Generate a compact diff between the current branch and its base branch,
replacing moved code blocks with summary comments.

Usage:
    mcp-coder git-tool compact-diff [--project-dir PATH] [--base-branch BRANCH] [--exclude PATTERN]

Options:
    --project-dir PATH      Project directory (default: current directory)
    --base-branch BRANCH    Base branch to diff against (default: auto-detected)
    --exclude PATTERN       Exclude paths matching pattern (repeatable)

Exit codes:
    0  Success — compact diff printed to stdout
    1  Could not detect base branch
    2  Error (invalid repo, unexpected exception)

Example:
    mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"
```

### `docs/architecture/architecture.md`

In the `utils/git_operations` section (or equivalent), add a brief note:

> `compact_diffs.py` — two-pass compact diff pipeline; internal module used by
> the `git-tool compact-diff` CLI command. Not exported from `__init__.py`.

### `README.md`

Add one sentence or bullet under an appropriate existing section (e.g. CLI
features or tools):

> **Compact diff** (`mcp-coder git-tool compact-diff`): reduces large refactoring
> diffs for LLM review by replacing moved code blocks with summary comments.

---

## HOW

- Read each file first to find the right insertion point before editing.
- Keep changes minimal — one section addition per file.
- No new files, no test changes.

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md.

Implement Step 5 exactly as specified.

Files to modify:
  docs/cli-reference.md
  docs/architecture/architecture.md
  README.md

For each file:
1. Read the file first to find the appropriate insertion point.
2. Add the content described in step_5.md, matching the existing style.
3. Keep additions concise — one focused addition per file.

Do not modify any other files. No tests needed for this step.
```
