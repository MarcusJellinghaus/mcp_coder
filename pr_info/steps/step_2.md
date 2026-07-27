# Step 2 — JSONC preprocessor (`_strip_jsonc`)

See [summary.md](./summary.md). A stdlib, string/escape-aware comment stripper
that also tolerates trailing commas. This is a security surface: comment-like
sequences inside strings (URLs, `"a // b"`, escaped quotes) must survive intact.

## WHERE
- Create `src/mcp_coder/icoder/permissions/loader.py`.
- Create `tests/icoder/test_permissions_loader.py`.

## WHAT
```python
def _strip_jsonc(text: str) -> str:
    """Strip // and /* */ comments and trailing commas from JSONC text.

    String/escape-aware: comment markers and commas inside string literals
    are preserved. Returns text suitable for json.loads.
    """
```

Module header (create the file now, with `from __future__ import annotations`
and a module docstring; `json`/`jsonschema` imports arrive in later steps as
needed — Step 2 needs neither).

## HOW
- Pure function, no imports beyond stdlib. Single left-to-right scan.

## ALGORITHM
```
out = []; i = 0; in_str = False; esc = False
while i < len(text):
    c = text[i]
    if in_str:                      # inside "...": copy verbatim, track escape
        out.append(c); esc = (c == '\\' and not esc); in_str = c != '"' or esc
    elif c == '"': in_str = True; out.append(c)
    elif c == '/' and peek == '/': skip until '\n'
    elif c == '/' and peek == '*': skip until '*/'
    elif c in '}]':                 # drop a trailing comma before this bracket
        back over trailing whitespace in out; if last is ',', delete it; out.append(c)
    else: out.append(c)
    i += 1
return ''.join(out)
```
(Keep the `in_str`/`esc` bookkeeping simple and correct — mirror the pseudocode
carefully; add a couple of inline comments.)

## DATA
Returns a comment-free, trailing-comma-free JSON string.

## TESTS (write first)
- `//` line comment and `/* */` block comment removed; resulting JSON parses.
- `"https://example.com"` preserved (double-slash inside string untouched).
- `"a // b"` and `"a /* b */ c"` preserved.
- Escaped quote inside string (`"he said \"hi\" //x"`) — trailing `//x` outside
  the string is stripped, the escaped quote survives.
- Trailing comma before `}` and `]` removed; comma inside a string (`"a,]"`)
  preserved.
- No-comment input returned effectively unchanged (round-trips via json.loads).

## VERIFICATION
All four MCP checks pass (pylint, pytest unit subset, mypy, ruff-docstrings).

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2
> with TDD: first write `tests/icoder/test_permissions_loader.py` covering the
> listed adversarial JSONC cases, then create
> `src/mcp_coder/icoder/permissions/loader.py` with the module header and a pure
> `_strip_jsonc(text: str) -> str` per the algorithm. Use MCP workspace file
> tools. Run `run_pylint_check`, `run_pytest_check` (unit subset), and
> `run_mypy_check`; fix until all pass. Single commit.
