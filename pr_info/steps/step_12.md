# Step 12 — Docs: toolkits, toolkit interface, migration note, transitional links (Scope 8)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_12.md`).
> Implement Step 12 only: documentation. Replace the "Until the next breaking
> release" section of `docs/configuration/toolkits.md` with documented
> behaviour, update `docs/architecture/toolkit-interface.md`, add the new
> section to `docs/migration/multi-language.md`, and fix every link to
> `#until-the-next-breaking-release`. Describe what the code now does (read it
> if in doubt). Run the fast pytest set (docs tests may exist). One commit.

## WHERE / WHAT

### `docs/configuration/toolkits.md`
- Delete `## Until the next breaking release` (table + "Other pages link here").
- "Configure a toolkit":
  - "No table configured" bullet → no table, or a table without `toolkit`, is
    an error with the snippets and a link to this section.
  - The sentence "at least `format` unless formatting is off, or `mcp-coder
    verify` fails" → "the actions and depths its bindings request (with the
    default bindings more than `format`, e.g. `test@quick` / `test@unattended`),
    or `mcp-coder verify` fails".
- Key table: `toolkit` default → "required".
- Rules list of `## [tool.mcp-coder.toolkit]`: drop "or a `command` subtable in a
  table without `toolkit`" from the unknown-key sentence; a table without
  `toolkit` is the no-toolkit error.
- "Bindings" rules: drop `check_type_hints` from the "read from pyproject.toml
  only" sentence; the "Which actions `mcp-coder verify` checks" bullet → every
  action of a non-empty binding (format only while `format_code` is on), plus
  one row per requested depth; check/test `error` items are warnings unless
  global or only one action returns.
- "mcp-tools-py" section: install via `mcp-coder[python]`; missing-extra hint.
- "Command toolkit → Errors": `verify` now runs `verify()` for check/test too
  (shown as warnings when two or more actions return), and reports undeclared
  requested depths; run time still returns `error`.
- Required MCP servers: `mcp-workspace` plus the servers the toolkit's
  `llm_permissions` name; a non-Python repo drops `mcp-tools-py` from `.mcp.json`
  (every `.mcp.json` server is still fatal at session start).

### `docs/architecture/toolkit-interface.md`
- Remove the `MCP_SERVER_NAMES` gotcha (~line 197); describe `required_mcp_servers`.
- Remove the hidden `formatter` item note and authoring-guide item 5 ("don't
  name an item `formatter`").
- `verify` callers: `verify_toolkit_rows.toolkit_rows` (per action) and the
  format pre-flight (`format` only).
- Fix the two links to the transitional section (~lines 146, 167).

### `docs/migration/multi-language.md`
- New section, e.g. `## A toolkit is required; mcp-tools-py is optional (#1199)`:
  no-toolkit error; `mcp-coder[python]`; required servers; non-Python repos drop
  `mcp-tools-py` from `.mcp.json`; `verify` checks every binding; `check_type_hints`
  retired → bindings (`implement_task = []`, `implement_final = ["test@quick"]`
  for repos without mypy); stage "Final checks", sessions `step_N_check_M`.
- Drop the "#1199 extends this note" line.
- Rewrite line ~16 ("Set `check_type_hints = false` …") to the bindings replacement.

### Pages linking `#until-the-next-breaking-release`
- `docs/architecture/architecture.md` (~line 60, "type-hint switch")
- `docs/processes-prompts/processes/05-implementation.md` (~line 40)
- Re-run `search_files(pattern="until-the-next-breaking-release")` until it has no match.

## HOW / ALGORITHM / DATA

Markdown edits only.

## Done when

`toolkits.md` has no "Until the next breaking release" section; nothing links
the anchor; `multi-language.md` documents this change.
