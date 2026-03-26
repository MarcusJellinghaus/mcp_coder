# Step 6: Update Documentation and Slash Commands

## Context
See `pr_info/steps/summary.md` for full issue context.

## Goal
Update all documentation and `.claude/commands/` slash command files to reference the new command names. Search-and-replace approach — no structural doc changes.

## LLM Prompt
```
Implement Step 6 of issue #570 (CLI restructure). Read pr_info/steps/summary.md for context, then read pr_info/steps/step_6.md for detailed instructions. Update documentation and slash commands to reflect new CLI structure. Run all code quality checks after changes.
```

## WHERE
- `docs/cli-reference.md` — major update for restructured commands
- `docs/coordinator-vscodeclaude.md` — update command references
- `docs/getting-started/label-setup.md` — `define-labels` → `gh-tool define-labels`
- `docs/configuration/config.md` — update config key references
- `.claude/commands/*.md` — update any command name references
- `tools/debug_vscode_sessions.py` — review for command name references

## WHAT

### docs/cli-reference.md
- Replace `coordinator run` with `coordinator` (direct command)
- Replace `coordinator test` with `coordinator --dry-run`
- Replace `coordinator vscodeclaude` with `vscodeclaude launch`
- Replace `coordinator vscodeclaude status` with `vscodeclaude status`
- Replace `coordinator issue-stats` with `gh-tool issue-stats`
- Replace `define-labels` (when used as standalone command) with `gh-tool define-labels`
- Update the command table/listing to match new structure

### docs/coordinator-vscodeclaude.md
- Replace `mcp-coder coordinator vscodeclaude` with `mcp-coder vscodeclaude launch`
- Replace `mcp-coder coordinator vscodeclaude status` with `mcp-coder vscodeclaude status`
- Replace `mcp-coder coordinator vscodeclaude --cleanup` with `mcp-coder vscodeclaude launch --cleanup`
- Replace `mcp-coder coordinator vscodeclaude --intervene` with `mcp-coder vscodeclaude launch --intervene`
- Update any config references: `[coordinator.vscodeclaude]` → `[vscodeclaude]`

### docs/getting-started/label-setup.md
- Replace `mcp-coder define-labels` with `mcp-coder gh-tool define-labels`

### docs/configuration/config.md
- Replace `[coordinator.vscodeclaude]` with `[vscodeclaude]`
- Update any references to `coordinator.vscodeclaude.workspace_base` etc.

### .claude/commands/*.md
- Search all files for: `coordinator run`, `coordinator test`, `coordinator vscodeclaude`, `coordinator issue-stats`, `define-labels`
- Replace with new command names per migration table

### tools/debug_vscode_sessions.py
- Review for any hardcoded command name strings and update

## HOW
Read each file, search for old command patterns, replace with new ones. This is pure documentation — no code logic changes.

## SEARCH PATTERNS
```
"coordinator run"           → "coordinator" (or "coordinator --all" / "coordinator --repo")
"coordinator test"          → "coordinator --dry-run"
"coordinator vscodeclaude"  → "vscodeclaude launch"  (unless followed by "status")
"coordinator vscodeclaude status" → "vscodeclaude status"
"coordinator issue-stats"   → "gh-tool issue-stats"
"define-labels"             → "gh-tool define-labels"  (when standalone command)
"[coordinator.vscodeclaude]" → "[vscodeclaude]"
"coordinator.vscodeclaude."  → "vscodeclaude."
```

## IMPORTANT NOTES
- Be careful with `define-labels` — only replace when it's used as a standalone command, not when it appears as a label name or in other contexts
- `coordinator` by itself might appear in many contexts — only replace `coordinator run`, `coordinator test`, etc. (the full subcommand forms)
- Check context before replacing to avoid false positives
