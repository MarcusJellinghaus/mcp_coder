# Step 1 — Remove `parsers.py` from `.large-files-allowlist`

**Single commit:** allowlist edit + verification passing.

See [summary.md](./summary.md) for the full context. This is the only step; the
task is a one-line deletion from a plain-text config file plus verification.

## WHERE

- **Modify:** `.large-files-allowlist` (project root)
- **No Python source files are touched.**

The entry to remove is the line:

```
src/mcp_coder/cli/parsers.py
```

It currently sits between `docs/processes-prompts/development-process.md` and
`tools/safe_delete_folder.py`. Remove **only** that line; leave every other line,
comment, and blank line exactly as-is.

## WHAT

No functions or signatures change. This is a text-file edit.

Use `mcp__mcp-workspace__edit_file`. The line `src/mcp_coder/cli/parsers.py` is
already unique in `.large-files-allowlist`, so a single-line edit is sufficient:
- `old_string`: `src/mcp_coder/cli/parsers.py`
- `new_string`: empty (removing that line).

## HOW (integration points)

- No imports, decorators, or code integration.
- The allowlist is consumed by `load_allowlist()` in
  `src/mcp_coder/checks/file_sizes.py`; removing the line makes `parsers.py` a
  normally-checked file. Since it is 560 lines (< 750), it will not become a
  violation.

## ALGORITHM

```
read .large-files-allowlist
locate the exact line "src/mcp_coder/cli/parsers.py"
delete that single line (keep surrounding entries/comments intact)
save file
```

## DATA

- **Input/Output:** plain-text file, one path per line. No data structures.
- **Post-condition:** `.large-files-allowlist` no longer contains
  `src/mcp_coder/cli/parsers.py`; all other entries preserved.

## TDD / Verification

There is no Python code to test, so TDD reduces to a **verification gate** rather
than a new unit test (writing a test that asserts a specific line is absent from a
config file would be brittle and is not warranted here — KISS).

Run the file-size check and confirm the acceptance criterion:

```
mcp-coder check file-size --max-lines 750
```

**Pass conditions:**
- `parsers.py` is **not** listed as a violation.
- `parsers.py` is **not** listed as a stale allowlist entry.
- The check still passes overall (`passed = len(violations) == 0`).

The two other stale entries (`vscodeclaude/workspace.py`,
`test_workspace_startup_script.py`) may still appear — that is expected and
**out of scope** (#1029). Do not touch them.

## Commit

One commit containing the single-line removal from `.large-files-allowlist`.

Suggested message:

```
chore(allowlist): remove parsers.py from large-files-allowlist (#1023)

parsers.py is 560 lines (<750) after #90; drop its stale allowlist entry.
```
