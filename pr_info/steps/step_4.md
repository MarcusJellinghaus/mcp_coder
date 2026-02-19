# Step 4: Update `implementation_review.md` + delete prototype tools

## Goal

Wire the new CLI command into the slash command used for code review, and remove
the two now-superseded standalone prototype scripts.

---

## WHERE

**Modify:** `.claude/commands/implementation_review.md`

**Delete:** `tools/git-refactor-diff.py`

**Delete:** `tools/compact_diff.py`

No tests required for this step (no code logic).

---

## WHAT

### `.claude/commands/implementation_review.md`

**Change 1 — `allowed-tools` frontmatter:**

Remove:
```yaml
Bash(git diff:*)
```
Add:
```yaml
Bash(mcp-coder git-tool compact-diff:*)
```

**Change 2 — diff command in body:**

Replace:
```bash
git diff --unified=5 --no-prefix ${BASE_BRANCH}...HEAD -- . ":(exclude)pr_info/.conversations/**"
```
With:
```bash
mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"
```

The `BASE_BRANCH` variable assignment line above it (`BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)`) is **not needed anymore** — `compact-diff` auto-detects the base branch internally. Remove that line too.

Final body section becomes:
```
Run this command to get the changes to review:
```bash
mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"
```
```

---

## HOW

- No imports or code changes — this is a markdown/YAML edit only.
- The `tools/` files have no dependents (they are standalone scripts). Verify
  nothing in `src/` or `tests/` imports them before deleting.

---

## VERIFICATION BEFORE DELETING TOOLS

Check that neither prototype file is imported anywhere:
```bash
grep -r "compact_diff\|git-refactor-diff\|git_refactor_diff" src/ tests/
```
Expected result: no matches (they were always standalone scripts).

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement Step 4 exactly as specified.

Actions:
1. Edit .claude/commands/implementation_review.md:
   a. In the frontmatter allowed-tools list, remove "Bash(git diff:*)" and add
      "Bash(mcp-coder git-tool compact-diff:*)".
   b. In the body, remove the BASE_BRANCH variable assignment line.
   c. Replace the git diff command with:
      mcp-coder git-tool compact-diff --exclude "pr_info/.conversations/**"

2. Before deleting the tools, verify they are not imported anywhere in src/ or tests/.

3. Delete tools/git-refactor-diff.py and tools/compact_diff.py.

Do not modify any other files.
```
