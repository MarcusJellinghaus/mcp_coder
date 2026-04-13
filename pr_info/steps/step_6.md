# Step 6: Docs + stale import verification

**Commit message:** `adopt mcp-coder-utils: add shared-libraries note to CLAUDE.md`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step adds a one-liner to CLAUDE.md and verifies no stale import paths remain.

## WHERE

- `.claude/CLAUDE.md`

## WHAT

### CLAUDE.md update
Add a one-liner in an appropriate section noting that `subprocess_runner`, `subprocess_streaming`, and `log_utils` are thin shims over `mcp-coder-utils` — always import through the local shims (`mcp_coder.utils.*`), enforced by import-linter.

### Stale import grep
Verify there are no direct imports of `mcp_coder_utils` outside the 3 shim files. This is already enforced by the import-linter contract from step 4, but a manual grep confirms nothing was missed.

Also verify no remaining references to deleted symbols like `_redact_for_logging` (outside deleted test files).

## HOW

Add a short note under a relevant section in CLAUDE.md, e.g. near the MCP tools section or as a new subsection:

```markdown
## 📦 Shared Libraries

`subprocess_runner`, `subprocess_streaming`, and `log_utils` in `src/mcp_coder/utils/` are thin shims over `mcp-coder-utils`. Always import through the local shims (`from mcp_coder.utils.<module> import ...`), not from `mcp_coder_utils` directly. Enforced by import-linter (`mcp_coder_utils_isolation` contract).
```

## ALGORITHM

```
1. Add shared-libraries note to CLAUDE.md
2. Grep for "mcp_coder_utils" in src/ — should only appear in 3 shim files
3. Grep for "_redact_for_logging" — should have zero hits
4. Grep for "from mcp_coder_utils" in tests/ — should have zero hits
```

## DATA

No code changes. Documentation only.

## VERIFICATION

- CLAUDE.md has the new note
- No stale imports found
- Run pylint, mypy, pytest (final confirmation everything passes)

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md.

Implement step 6: Add a shared-libraries one-liner to .claude/CLAUDE.md.
Then grep the codebase for stale import paths: "mcp_coder_utils" should only
appear in the 3 shim files, "_redact_for_logging" should have zero hits.
Run all checks after.
```
