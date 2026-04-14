# Step 4: Documentation — `docs/icoder/icoder.md`

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #808).

## Goal

Create `docs/icoder/icoder.md` documenting the iCoder TUI features: slash commands, status line (tokens, version, input hint), busy indicator, and input behavior. This fulfills decision #9.

## LLM Prompt

```
Implement Step 4 of Issue #808 (see pr_info/steps/summary.md for context).

Create docs/icoder/icoder.md documenting the iCoder TUI:
- Slash commands (/info, /help, /clear, /quit)
- Status line (tokens, version, input hint) — the new three-zone layout
- Busy indicator line (spinner, elapsed time)
- Input behavior (\ + Enter for newline)

Use the existing docs/iCoder.md as reference for content that can be
reused or referenced. The new doc focuses on TUI features specifically.
Run all three code quality checks after changes (no code changes, but verify nothing broke).
```

## WHERE

- **Create**: `docs/icoder/icoder.md`

## WHAT

Document structure:

```markdown
# iCoder TUI Reference

## Status Line
- Three-zone layout: tokens | version | input hint
- Token format: ↓<in> ↑<out> | total: ↓<in> ↑<out>
- Compact suffixes: k (thousands), M (millions)
- Initial state: ↓0 ↑0 | total: ↓0 ↑0
- Hidden when provider doesn't supply token data

## Slash Commands
- /help, /clear, /quit, /exit, /info
- Autocomplete with Tab

## Busy Indicator
- Shows spinner + elapsed time during LLM requests
- Shows tool name during tool execution

## Input Behavior
- Enter = submit
- \ + Enter = newline
- Shift+Enter = newline (terminal-dependent)
```

## HOW

- Reference existing `docs/iCoder.md` for command details and backslash escape docs
- Keep concise — this is a reference doc, not a tutorial
- No code changes in this step

## DATA

No code changes. Documentation only.
