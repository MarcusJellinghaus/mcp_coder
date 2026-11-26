# Step 5 — `persist.py` chooses its newline via `dominant_newline`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` exactly. TDD: write the test first, then change `_read`. Keep the atomic write and the no-normalisation behaviour. Run `run_format_code`, then pylint, pytest (`-n auto`, unit markers from CLAUDE.md), mypy, ruff, lint-imports, tach and vulture via the MCP tools. All must pass. This step is one commit.

## WHERE

- `src/mcp_coder/icoder/permissions/persist.py` (`_read`, and the docstrings of `_insert_item` / `_insert_section`)
- `tests/icoder/test_permissions_persist.py`

## WHAT

### Test first — `tests/icoder/test_permissions_persist.py`

Add it after `test_crlf_newlines_are_preserved`:

```python
def test_mixed_newlines_follow_the_dominant_ending(tmp_path: Path) -> None:
    # Mostly LF with one CRLF: inserted line breaks are LF, the CRLF stays.
    target = _seed(
        tmp_path, '{\n  "ask": [\r\n    "mcp__a__x"\n  ],\n  "allow": []\n}\n'
    )

    write_rule(target, OTHER, "deny")  # scaffold path builds its own newlines

    raw = target.read_bytes()
    assert raw.count(b"\r\n") == 1          # existing CRLF kept (no normalisation)
    assert b'"deny": [\n' in raw            # new block uses LF
```

Under the old rule ("CRLF if any `\r\n`") the new block would have used CRLF, so this test fails before the change.

### Implementation — `_read`

- Import: `from mcp_coder.utils.fs import dominant_newline`. The module already uses absolute `mcp_coder.` imports, and no import-linter contract blocks this one.
- Change the last line:

```python
    return text, dominant_newline(raw) or "\n"
```

- `_read` docstring, `Returns:` → `The decoded text and its newline style: the file's dominant ending, else LF (tie or no line breaks).`
- `_insert_item` / `_insert_section` docstrings, `newline:` arg → `The file's dominant ending ("\n", "\r\n" or "\r").`

## HOW

- `_atomic_write` (temp file + `os.replace`, `newline=""`) stays unchanged. Do not use `write_text`, because it would normalise existing line endings.
- A missing file already returns `(_NEW_FILE, "\n")`; leave that unchanged.

## ALGORITHM

```
raw = target.read_bytes()            # missing -> (_NEW_FILE, "\n")
text = raw.decode("utf-8")           # error -> PersistError
return text, dominant_newline(raw) or "\n"
```

## DATA

`_read(target) -> tuple[str, str]`, where the newline is `"\n"`, `"\r\n"` or `"\r"`.

## Commit message

`fix(icoder): persist chooses the dominant newline of the settings file`
