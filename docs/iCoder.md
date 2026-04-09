# iCoder User Guide

iCoder is an interactive TUI (Terminal User Interface) for conversing with LLMs.
Built on [Textual](https://textual.textualize.io/), it provides streaming responses,
slash commands with autocomplete, and multi-line input editing.

## Startup

Launch iCoder from the command line:

```bash
mcp-coder icoder
```

Common options:

```bash
mcp-coder icoder --project-dir /path/to/project
mcp-coder icoder --llm-method claude-code-cli
mcp-coder icoder --mcp-config .mcp.json
```

On startup iCoder:

1. Resolves the project directory and sets up environment variables
2. Verifies MCP server availability
3. Auto-resumes the latest LLM session (if one exists)
4. Displays runtime info (version, active venv, MCP servers)

## Commands

Type a slash command and press Enter:

| Command  | Description          |
|----------|----------------------|
| `/help`  | Show available commands and keyboard shortcuts |
| `/clear` | Clear the output log |
| `/quit`  | Exit iCoder          |
| `/exit`  | Exit iCoder (alias)  |

## Autocomplete

- Type `/` to see all available commands
- Continue typing to filter matches (e.g. `/h` shows `/help`)
- **Tab** — accept the highlighted suggestion
- **Up / Down** — navigate the suggestion list
- **Escape** — dismiss the dropdown

## Streaming

LLM responses stream into the output log in real time. Tool-use actions
(file reads, edits, shell commands) are displayed as they execute so you
can follow the assistant's progress.

## Keyboard Shortcuts

| Shortcut             | Action                                |
|----------------------|---------------------------------------|
| `\` + Enter          | Insert a newline                      |
| Shift+Enter          | Insert a newline (terminal support varies) |
| Up                   | Previous command from history (when on first line) |
| Down                 | Next command from history (when on last line)      |

## Backslash Escape Mechanism

On some terminals (notably Windows), Shift+Enter is indistinguishable from
Enter. The backslash escape provides a reliable alternative for multi-line input.

**Basic usage:** type a backslash at the end of your text, then press Enter.
Instead of submitting, iCoder strips the backslash and inserts a newline.

```
Hello world\↵       →  "Hello world" + newline (continue typing)
```

**Submitting with a literal trailing backslash:** use two backslashes.

```
path\to\dir\\↵      →  submits "path\to\dir\"
```

**Parity rule:** the behaviour depends on the number of consecutive trailing
backslashes:

| Trailing backslashes | Count | Parity | Result                          |
|----------------------|-------|--------|---------------------------------|
| `text\`              | 1     | odd    | Strip `\`, insert newline       |
| `text\\`             | 2     | even   | Strip one `\`, submit `text\`   |
| `text\\\`            | 3     | odd    | Strip one `\`, insert newline after `text\\` |
| `text\\\\`           | 4     | even   | Strip one `\`, submit `text\\\` |

In all cases exactly one trailing backslash is removed. Odd count → newline;
even count → submit.
