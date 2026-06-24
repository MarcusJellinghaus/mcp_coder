# iCoder TUI Reference

Quick reference for the iCoder terminal user interface.

## Status Line

A single-row bar at the bottom of the output log with three zones:

| Zone | Position | Content |
|------|----------|---------|
| Tokens | Left | `↓<in> ↑<out> \| total: ↓<in> ↑<out>` |
| Version | Centre | `mcp-coder v<version>` |
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
| `10s` | Branch + dirty state refresh; if the branch changed and the PR toggle is on, an automatic PR fetch is kicked. |
| `30s` | Full issue-cache reload (re-hits the GitHub API past the cache's 50s window). |
| Branch change | Auto PR fetch (only when toggle is on). |
| Button click | Manual refresh of issue or PR. |

### PR toggle

PR lookup is **off by default** and is **not persisted** between sessions.
The 10s auto-PR fetch only fires when the toggle is on. The `↻ PR` button,
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
| `/display oneline\|compressed` | Set the default tool-display tier (hard reset: also clears per-block toggles). |
| `/load` | Open a session picker to choose and resume a prior session |
| `/quit` | Exit iCoder |
| `/exit` | Exit iCoder (alias for `/quit`) |

### Session Picker

The session picker is a modal list of prior icoder logs in the project's
`logs/` directory, filtered to the current LLM provider. Each row shows
the log timestamp, provider, turn count, and the first prompt of that
session. It is reachable two ways:

- **At startup** via `icoder --continue-session`. The picker runs
  synchronously before the main TUI starts.
- **Mid-run** via `/load`.

Up/Down moves the highlight; Enter picks the session and resumes it
(restores the LLM session id, replays the prior UI history, and renders
a `────── Resumed ──────` divider followed by the current runtime
banner). Esc dismisses the picker without resuming.

`--continue-session-from FILE` skips the picker and resumes a specific
log; `FILE` must be a `.jsonl` event log. A legacy `.json` response file
is rejected with a hard error.

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

## Tool Display Tiers

Tool calls are rendered in one of three tiers:

| Tier | Name | What it shows |
|------|------|---------------|
| 1 | **oneline** | A single collapsed summary line (tool name, key arg, line/error count). |
| 2 | **compressed** | A boxed block with the args and a truncated output preview. |
| 3 | **detail modal** | A full-screen, read-only `TextArea` with the complete args and output. |

Interaction:

- **Left single click** on a tool block toggles it between tier 1 (oneline)
  and tier 2 (compressed). The toggle is debounced (~250 ms) so a double
  click never registers as a toggle first.
- **Double click** on any content block (tool, user input, or assistant
  turn) opens the tier-3 detail modal.
- **F2** opens the detail modal for the most recent content block.
- Inside the modal, **Escape** / **Enter** close it and **Ctrl+C** copies
  the current selection.

The global default tier is **compressed**. It can be set at startup with
`--tool-display=oneline|compressed` and changed at runtime with the
`/display oneline|compressed` slash command. `/display` is a *hard reset*:
it sets the new default **and** discards every per-block toggle.

## Input Behaviour

| Shortcut | Action |
|----------|--------|
| **Enter** | Submit message |
| **`\` + Enter** | Insert a newline (reliable on all terminals) |
| **Shift+Enter** | Insert a newline (terminal support varies) |
| **Up** | Previous command from history (cursor on first line) |
| **Down** | Next command from history (cursor on last line) |
| **F2** | Open the detail modal for the most recent content block |

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

## Log files

Each session writes two files in `logs/`: a structured
`icoder_<timestamp>.jsonl` (the authoritative replay log) and a sibling
`icoder_<timestamp>_chat.txt` mirroring the visible conversation in plain
text for copy/paste. The `.txt` is best-effort — if it cannot be opened
or written, iCoder continues with only the `.jsonl` and logs a warning.
