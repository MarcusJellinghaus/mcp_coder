# Refactoring Principles

Quick reference for refactoring rules and tools. For detailed process, examples, and checklists, see the [Safe Refactoring Guide](../../docs/processes-prompts/refactoring-guide.md).

## Key Rules

- **Move, don't change.** Logic changes belong in a separate PR.
- **Only adjust imports.** Use `move_symbol` — it updates imports automatically.
- **Clean deletion, no legacy artifacts.** No stubs, no re-exports for backward compatibility.
- **Small steps.** One module per PR. Keep diffs under 25,000 tokens.
- **Tests mirror source structure.**

## MCP Refactoring Tools

| Tool | Purpose |
|------|---------|
| `mcp__tools-py__list_symbols` | List top-level symbols in a file |
| `mcp__tools-py__find_references` | Find all references project-wide |
| `mcp__tools-py__move_symbol` | Move symbol + update all imports |
| `mcp__tools-py__rename_symbol` | Rename symbol + update all references |
| `mcp__tools-py__move_module` | Move entire module + update references |

## Verification Tools

| Tool | Purpose |
|------|---------|
| `mcp-coder git-tool compact-diff` | Suppress moved-code blocks in diff — remaining diff should be imports only |
| `mcp-coder check file-size --max-lines 750` | Verify all files are under the size threshold |

See [Safe Refactoring Guide — Verification](../../docs/processes-prompts/refactoring-guide.md#step-4-verify) for the full checklist.
