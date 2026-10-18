# Step 1: Add `write_lf_text` helper

See `pr_info/steps/summary.md` for the full design rationale.

## Precondition

`src/mcp_coder/utils/text_io.py` must not already exist. If it does, write
one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Create `src/mcp_coder/utils/text_io.py`
- Create `tests/utils/test_text_io.py`

No existing files are modified in this step — this is a standalone helper
with no callers yet (callers are switched in Steps 2-5).

## WHAT

```python
def write_lf_text(path: Path, text: str, *, append: bool = False) -> None:
    """Write text to path with LF-only line endings, never CRLF."""
```

- `path`: target file (parent directory must already exist — the helper does
  not create directories, matching every current call site).
- `text`: content to write; any embedded `\r\n` is normalized to `\n` first.
- `append`: `False` writes (truncates), `True` appends. Keyword-only.
- Returns `None`.

Contract (document as a short docstring note, not multi-paragraph): this is a
pure write — it does not guard against a lone `\r` (not `\r\n`) in `text`;
only `\r\n` is normalized.

## HOW

- Module has no project imports beyond `pathlib.Path` — it is a leaf utility.
- No decorators, no integration points in this step.

## ALGORITHM

```
normalized = text.replace("\r\n", "\n")
mode = "a" if append else "w"
with path.open(mode, encoding="utf-8", newline="\n") as handle:
    handle.write(normalized)
```

## DATA

No return value. Side effect: `path` on disk contains `normalized`, written
as bytes with `\n` line endings only (verified by `read_bytes()` in tests).

## Tests (write first)

In `tests/utils/test_text_io.py`:

1. `test_write_mode_writes_lf_only_bytes` — `write_lf_text(path, "a\nb\n")`;
   assert `path.read_bytes() == b"a\nb\n"`.
2. `test_write_mode_normalizes_embedded_crlf` —
   `write_lf_text(path, "a\r\nb\r\n")`; assert
   `path.read_bytes() == b"a\nb\n"`.
3. `test_append_mode_appends_without_truncating` — call once with
   `"a\n"`, then again with `append=True, text="b\n"`; assert
   `path.read_bytes() == b"a\nb\n"`.
4. `test_append_mode_normalizes_embedded_crlf` — same as #3 but the appended
   chunk contains `"c\r\n"`; assert the appended bytes contain no `\r`.
5. `test_open_called_with_newline_lf` — a spy test. Monkeypatch
   `pathlib.Path.open` to a wrapper that records `kwargs` then delegates to
   the original bound method, call `write_lf_text(path, "x\n")`, assert the
   captured `kwargs["newline"] == "\n"`. This is the test that fails on every
   OS (not just Windows) if the helper stops passing `newline="\n"`.

6. `test_lf_only_input_is_written_byte_identical` — parametrized over
   `append in (False, True)` and `text in ("", "no newline", "a\nb", "a\n\nb\n")`.
   For `append=True`, pre-seed the file with `b"seed\n"` and assert
   `read_bytes() == b"seed\n" + text.encode()`; for `append=False`, assert
   `read_bytes() == text.encode()`. This pins the contract that LF-only input
   is never altered (no added/removed trailing newline, no other rewrite) in
   either mode — tests 1 and 3 cover the common case, this one covers edges.

Example for test 5:

```python
def test_open_called_with_newline_lf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "f.txt"
    original_open = Path.open
    captured: dict[str, object] = {}

    def spy(self: Path, *args: object, **kwargs: object) -> object:
        captured.update(kwargs)
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy)
    write_lf_text(path, "x\n")
    assert captured["newline"] == "\n"
```

Then implement `write_lf_text` in `src/mcp_coder/utils/text_io.py` to make
all tests pass.

## Checks

Run, in order, and fix anything that fails before committing:

- `mcp__mcp-tools-py__run_pytest_check` (unit markers excluded per
  CLAUDE.md), scoped to `tests/utils/test_text_io.py`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_tach_check`
- `mcp__mcp-tools-py__run_lint_imports_check`
- `mcp__mcp-tools-py__run_format_code`

## Commit

One commit: `feat(utils): add write_lf_text helper for LF-only committed-file writes`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file
> (`pr_info/steps/step_1.md`). Implement Step 1 exactly as specified: write
> the tests in `tests/utils/test_text_io.py` first, confirm they fail, then
> implement `write_lf_text` in `src/mcp_coder/utils/text_io.py` to make them
> pass. Run the checks listed under "Checks" and fix any failures. Do not
> touch any other file — callers are switched in later steps. Format code,
> then make exactly one commit for this step.
