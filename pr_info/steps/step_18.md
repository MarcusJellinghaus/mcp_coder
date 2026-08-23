# Step 18 — Smart-quote hint in `_format_toml_error`

`_format_toml_error` (`user_config.py`) already hints on Windows backslash
escaping. Curly/smart quotes — pasted from a chat window or a document — were one
of the reported failure modes and produce an opaque TOML parse error.

## WHERE

- `src/mcp_coder/utils/user_config.py` — `_format_toml_error` only
- `tests/utils/test_user_config.py`

## WHAT

No signature change:

```python
def _format_toml_error(file_path: Path, error: tomllib.TOMLDecodeError) -> str: ...
```

## HOW

- The function already reads the offending line from the file to render the
  `^` pointer. Reuse that same `error_line` — no second read.
- Add the check beside the existing backslash hint, using the same
  blank-line-then-`Hint:` shape so both render consistently. Both hints may
  appear together; that is fine.
- Characters to detect: `“ ” ‘ ’` (U+201C, U+201D, U+2018, U+2019).
- Guard the whole thing: when the line could not be read, skip silently (the
  existing `except OSError` path leaves no line content).

## ALGORITHM

```
_SMART_QUOTES = "\u201c\u201d\u2018\u2019"
...
if error_line and any(ch in error_line for ch in _SMART_QUOTES):
    lines += ["", "Hint: Curly/smart quotes are not valid TOML string delimiters.",
              '  Use straight quotes: "value" or \'value\'']
```

## DATA

```
  File "C:/Users/x/.mcp_coder/config.toml", line 7
    base_url = “https://relay/v1”
               ^
TOML parse error: Invalid value (at line 7, column 12)

Hint: Curly/smart quotes are not valid TOML string delimiters.
  Use straight quotes: "value" or 'value'
```

## TDD

1. A config whose value uses `“…”` → the formatted error contains the
   smart-quote hint.
2. A config with an unescaped Windows backslash → the existing backslash hint
   still appears and the smart-quote hint does not.
3. A plain syntax error (e.g. missing `=`) → neither hint.
4. Unreadable file → no crash, no hint (existing `OSError` path preserved).

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_18.md`.
> Implement step 18: extend `_format_toml_error` in `utils/user_config.py` with a
> curly/smart-quote hint (U+201C/U+201D/U+2018/U+2019), detected on the error line
> it already reads, rendered beside the existing backslash hint in the same
> style. Do not change the signature and do not re-read the file. Write tests
> first (TDD), covering both hints independently and the no-hint case.
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
