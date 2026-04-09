# Step 4 — `docs/iCoder.md` user guide

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Create `docs/iCoder.md` — comprehensive but concise user guide.

## WHERE

- **Create:** `docs/iCoder.md`

## WHAT

Sections to cover (concise, not verbose):

1. **Overview** — what iCoder is (interactive TUI for LLM conversations)
2. **Startup** — how to launch (`mcp-coder icoder`), env setup, runtime info display
3. **Commands** — `/help`, `/clear`, `/quit` with brief descriptions
4. **Autocomplete** — type `/` to trigger, Tab to accept, Escape to dismiss
5. **Streaming** — LLM responses stream in real-time, tool use display
6. **Keyboard shortcuts** — the main content for this issue:
   - `\ + Enter` — insert newline
   - `Shift+Enter` — insert newline (terminal support varies)
   - `\\` + Enter — submit with literal trailing `\`
   - Multiple backslashes: parity-based (odd → newline, even → submit)
   - Up/Down — command history navigation
7. **Backslash escape mechanism** — detailed explanation with examples

## HOW

Plain markdown file. No code changes. Reference existing commands from the registry.

## DATA

No code data structures. Documentation only.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Create docs/iCoder.md — a comprehensive but concise user guide for iCoder.

1. Write the document covering all sections listed in step_4.md.
2. Keep it practical — examples over explanations.
3. Run code quality checks to ensure nothing broke.
4. Commit: "docs: add iCoder user guide (#754)"
```
