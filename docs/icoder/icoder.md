# iCoder TUI Reference

Quick reference for the iCoder terminal user interface.

## Status Line

A single-row bar at the bottom of the output log with three zones:

| Zone | Position | Content |
|------|----------|---------|
| Tokens | Left | `↓<in> ↑<out> \| total: ↓<in> ↑<out>` |
| Version | Centre | `v<version>` |
| Input hint | Right | `\ + Enter = newline` |

- Token counts use compact suffixes: **k** (thousands), **M** (millions)
- Initial state: `↓0 ↑0 | total: ↓0 ↑0`
- The token zone is hidden when the LLM provider does not supply usage data

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and keyboard shortcuts |
| `/info` | Show runtime diagnostics (version, venv, MCP servers, env vars) |
| `/clear` | Clear the output log |
| `/quit` | Exit iCoder |
| `/exit` | Exit iCoder (alias for `/quit`) |

### Autocomplete

- Type `/` to see all commands
- Continue typing to filter (e.g. `/h` → `/help`)
- **Tab** — accept the highlighted suggestion
- **Up / Down** — navigate the list
- **Escape** — dismiss

## Busy Indicator

A single-row line below the output log:

- **Idle**: `✓ Ready`
- **LLM streaming**: spinner + `Thinking…` + elapsed time (e.g. `⠹ Thinking… [3.2s]`)
- **Tool execution**: spinner + tool name + elapsed time (e.g. `⠧ Running tool [1.5s]`)

The spinner animates at ~7 fps using braille dot characters.

## Input Behaviour

| Shortcut | Action |
|----------|--------|
| **Enter** | Submit message |
| **`\` + Enter** | Insert a newline (reliable on all terminals) |
| **Shift+Enter** | Insert a newline (terminal support varies) |
| **Up** | Previous command from history (cursor on first line) |
| **Down** | Next command from history (cursor on last line) |

### Backslash Escape Details

The backslash escape handles trailing backslashes via a parity rule:

| Trailing `\` | Count | Result |
|--------------|-------|--------|
| `text\` | 1 (odd) | Strip `\`, insert newline |
| `text\\` | 2 (even) | Strip one `\`, submit `text\` |
| `text\\\` | 3 (odd) | Strip one `\`, insert newline after `text\\` |
| `text\\\\` | 4 (even) | Strip one `\`, submit `text\\\` |

In all cases exactly one trailing backslash is removed. Odd count → newline;
even count → submit.
