# Decisions

Decisions from plan review discussion.

| # | Topic | Decision | Rationale |
|---|-------|----------|-----------|
| 1 | Delete Linux templates | Yes — remove in Step 2 | Clean up dead code while touching templates.py |
| 2 | Merge Step 4 into Step 3 | No — keep 4 separate steps | Each step stays cleanly scoped |
| 3 | Parameterize `{step_number}` in `AUTOMATED_SECTION_WINDOWS` | Yes | Consistency with other templates |
| 4 | Single-command UX for status-07 | Fully interactive from start | Solves timeout problem; intended behavior |
| 5 | `timeout` parameter for single-command flows | Keep parameter, note in docstring it's unused for single-command | API compatibility |
| 6 | Edge cases for `commands` field | Three cases: (a) `commands` absent → no session created, (b) `commands: []` → bare environment with no command sections, (c) invalid JSON (e.g. commands is string, contains non-strings) → raise error. All three tested and documented. | Fail fast on bad config, permissive on valid-but-empty |
| 7 | Schema docs for `labels.json` | Add concise `labels_schema.md` next to `labels.json` in Step 1 | No existing docs for the `vscodeclaude` block |
