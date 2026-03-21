# Step 2: Update Development Process Documentation

**Reference:** See `pr_info/steps/summary.md` for full context.

## LLM Prompt

> Implement Step 2 from `pr_info/steps/summary.md`.
> Add a "Failure Handling" section to `docs/processes-prompts/development-process.md` documenting the 5 failure labels, when they're triggered, and recovery paths.
> After making changes, run pylint, pytest (unit tests only), and mypy checks.

## WHERE

- `docs/processes-prompts/development-process.md` — add new section after section 7

## WHAT

Add a concise "8. Failure Handling" section containing:

1. A brief intro paragraph explaining failure labels
2. A table of all 5 failure labels with: label name, trigger condition, recovery action
3. A short note on recovery (use `mcp-coder set-status` to transition back to a retry-ready state)

## HOW

- Append new section `### 8. Failure Handling` at the end of the document (after section 7)
- Keep it concise — one table, two short paragraphs
- Reference the existing `set-status` command for recovery

## ALGORITHM

```
1. Read development-process.md
2. Find end of section 7 (PR Review & Merge)
3. Append section 8 with failure handling table and recovery docs
4. Run quality checks (no Python changes, but verify no broken formatting)
```

## DATA

Failure label reference table content:

| Label | Triggered When | Recovery |
|-------|---------------|----------|
| `status-03f:planning-failed` | Plan generation fails | `set-status status-02:awaiting-planning` |
| `status-06f:implementing-failed` | General implementation failure | `set-status status-05:plan-ready` |
| `status-06f-ci:ci-fix-needed` | CI exhausted 3 fix attempts | `set-status status-05:plan-ready` |
| `status-06f-timeout:llm-timeout` | LLM API timeout | `set-status status-05:plan-ready` |
| `status-09f:pr-creating-failed` | PR creation fails | `set-status status-08:ready-pr` |
