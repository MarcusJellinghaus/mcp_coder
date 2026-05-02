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

## Branch Info

A two-row info area below the status line summarising the current branch,
its linked GitHub issue, optional PR number, and cache freshness. Three
controls let the user refresh manually and toggle PR lookup on/off.

### Fields

| Zone | Example | Notes |
|------|---------|-------|
| Branch · State | `123-foo · dirty · (no issue)` | Branch name, working-tree state (`clean`/`dirty`), and `(no issue)` when the branch has no linked issue. Outside a git repo: `(no git)`. |
| Issue | `#123 Fix things  status-04:plan-review` | Issue number, title, and status pill (color from `labels.json`). |
| PR | `PR #45` / `PR —` / `—` | `PR #N` when known, `PR —` when toggle is on but no PR exists, `—` when the toggle is off or the branch has no issue. |
| Cache age | `(2m ago)` | Minute-granularity stamp of the last issue-cache refresh. |

Placeholder semantics across all zones:

- `…` — fetch in flight
- `?` — fetch failed
- `—` — not applicable

### Buttons

| Button | Action |
|--------|--------|
| `↻ issue` | Re-fetch the linked issue (fires regardless of toggle) |
| `↻ PR` | Re-fetch the PR for the linked issue (fires regardless of toggle) |
| `PR:on\|off` | Toggle automatic PR lookup on/off |

### Update cadence

| Trigger | What runs |
|---------|-----------|
| `2s` | Branch + dirty state refresh; if the branch changed and the PR toggle is on, an automatic PR fetch is kicked. |
| `30s` | Full issue-cache reload (re-hits the GitHub API past the cache's 50s window). |
| Branch change | Auto PR fetch (only when toggle is on). |
| Button click | Manual refresh of issue or PR. |

### PR toggle

PR lookup is **off by default** and is **not persisted** between sessions.
The 2s auto-PR fetch only fires when the toggle is on. The `↻ PR` button,
in contrast, fires regardless of the toggle state — it is a manual
override.

A monotonic generation token guards against stale results: toggling off
mid-fetch (or starting a newer fetch) invalidates the in-flight worker so
its result is silently discarded.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and keyboard shortcuts |
| `/info` | Show runtime diagnostics (version, venv, MCP servers, env vars) |
| `/clear` | Clear the output log |
| `/color [name\|hex]` | Change prompt border color. No args lists available colors. |
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
