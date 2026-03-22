# Step 9: Missing Returns — Batch 2 (llm, utils, workflows, workflow_utils)

> **Context:** See [summary.md](summary.md). DOC201 violations split into two batches to avoid timeout.

## Goal

Add missing `Returns` sections to docstrings in the remaining `src/` packages.

## Rules Addressed

| Rule | Description |
|------|-------------|
| DOC201 | Missing `Returns` section in docstring |

## Discovery

```bash
# Get remaining DOC201 violations (should only be in these directories after step 8)
ruff check src --select DOC201

# This step covers:
# src/mcp_coder/llm/
# src/mcp_coder/utils/
# src/mcp_coder/workflows/
# src/mcp_coder/workflow_utils/
# Any remaining src/ files not covered by step 8
```

## HOW

For each function with DOC201, read the implementation and add a `Returns:` section in Google-style format. Keep descriptions concise.

## Verification

- `ruff check src --select DOC201` — 0 violations across all of `src/`
- `pytest -n auto -m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"` — all pass

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_9.md for context.

Execute step 9: Add missing Returns sections (batch 2).

1. Run `ruff check src --select DOC201` to see remaining violations
2. In THIS step, fix files under:
   - src/mcp_coder/llm/
   - src/mcp_coder/utils/
   - src/mcp_coder/workflows/
   - src/mcp_coder/workflow_utils/
   - Any other remaining src/ files
3. For each function, read it and add a `Returns:` section in Google-style format
4. Run `./tools/format_all.sh`
5. Verify `ruff check src --select DOC201` reports 0 total violations
6. Run pylint, pytest, mypy checks
7. Commit the changes
```
