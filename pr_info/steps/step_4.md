# Step 4 — `permissions/persist.py`: comment-preserving JSONC write-back

> **Gated on step 1 (#1154).** A persisted grant is inert without the resolver fix.

## Goal

Insert exactly one matcher string into the correct top-level list of a JSONC settings file,
preserving comments, order, indentation, encoding and newline style. Pure library step — no UI
wiring (that is step 5).

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/persist.py` | **new** |
| `tests/icoder/test_permissions_persist.py` | **new**, unmarked, plain `tmp_path` |
| `.importlinter` | add the module to `permissions_leaf_isolation` `source_modules` |

## WHAT

```python
Section = Literal["allow", "ask", "deny"]

class PersistError(OSError):
    """Raised when the target file cannot be parsed or holds a section this
    writer refuses to edit. Subclasses OSError so the caller's existing degrade
    branch already covers it."""

class Span(NamedTuple):
    kind: str      # "code" | "string" | "comment"
    start: int
    end: int

def _scan(text: str) -> list[Span]: ...
def _find_section_array(text, spans, section) -> tuple[int, int] | None: ...
def _find_item(text, spans, open_i, close_i, matcher) -> Span | None: ...
def _locate_item(text, section, matcher) -> Span: ...   # None -> PersistError
def _insert_item(text, open_i, close_i, matcher, newline) -> str: ...
def _insert_section(text, spans, section, matcher, newline) -> str: ...
def _remove_item(text: str, span: Span) -> str: ...
def _atomic_write(target: Path, text: str) -> None: ...

def write_rule(target: Path, matcher: str, section: Section = "allow") -> None: ...
```

`write_rule(target, ...)` takes the path as a parameter even though v1 always passes
`.icoder/settings.local.json`: I4.2/#1048 plans a target override, and a parameterised entry point
means that screen need not reopen this module.

## HOW — integration points

```python
from mcp_coder.icoder.permissions.loader import _strip_jsonc
```

`_strip_jsonc` is reused as a **parser** — `json.loads(_strip_jsonc(text))` tells us what the file
already contains — but not as a **locator**: it returns a `str` with no offset mapping. The
locator is `_scan`, authored here from the same string/escape state machine. Importing the private
name across modules in the same package follows the existing precedent (`detail_modal.py` imports
`_render_value_full` from `stream_renderer`).

A JSON round-trip is rejected outright: comment preservation is a hard requirement.

`.importlinter` — add `mcp_coder.icoder.permissions.persist` to `permissions_leaf_isolation`'s
`source_modules` (lines 380–387). That list is explicit, not a `**` glob, so a new module is
otherwise silently unconstrained. Do **not** add it to `permissions_core_purity`: the writer needs
`json` and file I/O.

## ALGORITHM

`_scan` — one pass, three span kinds, offsets into the original text:

```
i = 0; code_start = 0; out = []
while i < n:
    if text[i] == '"':      flush code; walk to the closing quote honouring \\ escapes; emit "string"
    elif text[i:i+2]=='//': flush code; walk to the newline (exclusive);              emit "comment"
    elif text[i:i+2]=='/*': flush code; walk past the closing '*/';                   emit "comment"
    else: i += 1
flush the trailing code span
```

`_find_section_array` — depth is counted over **code spans only**, so a bracket inside a string or
a comment cannot move it:

```
depth = 0
for span in spans:
    if span is code:   depth += count("{[") - count("}]") over its chars
    elif span is string and depth == 1 and json.loads(span_text) == section:
        # Guard, not an assumption: a depth-1 string may be a *value*, not a key.
        walk code chars after the span, skipping whitespace:
            next non-space must be ':' , then the next non-space must be '['
            if either check fails -> NOT this key; continue the for-loop
        open_i = offset of that '['
        keep walking code chars counting '[' / ']' -> matching close_i
        return (open_i, close_i)
return None
```

**The `:` + `[` check must fall through, not bail.** `defaultMode` is a top-level key whose
schema enum is exactly `"allow" | "ask" | "deny"` (`loader.py::build_settings_schema`), so
`{"defaultMode": "allow", "allow": [...]}` puts a depth-1 string `"allow"` in the text that is a
*value*. Returning `None` there would make `write_rule` call `_insert_section` and emit a second
top-level `"allow"` key — a file that fails schema validation and degrades the whole config
fail-closed. Continuing the scan finds the real key later in the same pass.

`_insert_item` — two branches, no formatting engine:

```
body = text[open_i+1:close_i]
if "\n" not in text[open_i:close_i+1]:              # inline array: ["a"] -> ["new", "a"]
    return text[:open_i+1] + json.dumps(matcher) + (", " if body.strip() else "") + text[open_i+1:]
indent = indentation of the first existing item's line, else indent of the '[' line + "  "
return (text[:open_i+1] + newline + indent + json.dumps(matcher)
        + ("," if body.strip() else "") + text[open_i+1:])
```

Inserting immediately after `[` means the existing items, their comments and their indentation are
never touched — the diff is one added line.

`_insert_section` — key absent, so insert after the root `{`, one item per line (design §8.2):

```
root = offset of the first '{' in a code span
indent = indentation of the root line + "  "
comma = "" if the root object body holds no code characters else ","
block = f'{indent}"{section}": [{nl}{indent}  {json.dumps(matcher)}{nl}{indent}]{comma}'
return text[:root+1] + newline + block + text[root+1:]
```

`_remove_item` (the move case) — delete the item's span plus one adjacent comma, and drop the
whole line when nothing else remains on it.

`write_rule`:

```
text, newline = _read(target)                    # "{\n}\n", "\n" when the file is absent
try:
    data = json.loads(_strip_jsonc(text))
except ValueError as exc:                        # JSONDecodeError is a ValueError
    raise PersistError(f"{target} is not valid JSONC: {exc}") from exc
if not isinstance(data, dict):                   # e.g. a bare list or scalar root
    raise PersistError(f"{target} does not hold a JSON object")
for key in ("allow", "ask", "deny"):             # a present section must be a list
    if key in data and not isinstance(data[key], list):
        raise PersistError(f"{target}: {key!r} is not a list")
if matcher in data.get(section, []): return      # idempotent: no write, no mtime change
for other in ("allow","ask","deny") if other != section and matcher in data.get(other, []):
    span = _locate_item(text, other, matcher)    # raises PersistError, never returns None
    text = _remove_item(text, span)
arr = _find_section_array(text, _scan(text), section)
text = _insert_item(text, *arr, matcher, newline) if arr else _insert_section(text, ..., newline)
_atomic_write(target, text)
```

```
def _locate_item(text, section, matcher) -> Span:
    spans = _scan(text)
    found = _find_section_array(text, spans, section)
    if found is None:
        raise PersistError(f"{target}: cannot locate the {section!r} array to move {matcher!r}")
    item = _find_item(text, spans, *found, matcher)
    if item is None:
        raise PersistError(f"{target}: {matcher!r} parses inside {section!r} but has no locatable span")
    return item
```

**Neither `None` may reach an unpack or `_remove_item`.** `_find_section_array` returns
`tuple | None` and `_find_item` returns `Span | None`, while `_remove_item` takes a `Span`. The
`json.loads` view and the text locator can disagree — a duplicate top-level key
(`{"ask": [], "ask": ["mcp__a__b"]}` is valid JSON; `json.loads` keeps the second, the locator
returns the first, empty array) makes `_find_item` return `None`. Unguarded, that is a
`TypeError`, not an `OSError`, so it escapes step 5's single degrade branch, skips
`resolve_pending` and wedges the turn — the same failure mode the non-list-section guard below
exists to prevent. Converting both to `PersistError` before the write keeps the
one-failure-type contract true on this path too.

Re-run `_scan` after every mutation rather than adjusting offsets. A settings file is small and
this removes a whole class of off-by-one bugs.

**The section-type check is not defensive padding — it is what keeps the failure mode inside
`PersistError`.** `{"allow": "mcp__a__b"}` is valid JSON with an object root, so it clears both
guards above; then `matcher in data.get(section, [])` silently becomes a *substring* test over a
string, and once the move branch or the locator runs, `_find_section_array` finds no `"allow"`
followed by `:` `[`, returns `None`, and the `*_find_section_array(...)` unpack raises a
`TypeError` — not an `OSError`, so it escapes step 5's single degrade branch, skips
`resolve_pending` and wedges the turn. Rejecting a non-list section up front is one `isinstance`
and keeps the module's one-failure-type contract true. (Schema validation lives in the loader and
is not available here: the writer must not import `_schema_errors`' jsonschema path for one check.)

## DATA

- `_read(target) -> tuple[str, str]` uses `target.read_bytes().decode("utf-8")`, **not**
  `read_text()`, which applies universal-newline translation and would silently convert CRLF to
  LF. Newline style is one check: `"\r\n" if "\r\n" in raw else "\n"`.
  **The decode is inside the contract too.** `UnicodeDecodeError` is a `ValueError`, not an
  `OSError`, so a `settings.local.json` holding invalid UTF-8 would escape step 5's single
  `except OSError`, skip `resolve_pending` and wedge the turn — the same escape the parse,
  non-object-root, non-list-section and move-branch guards exist to close, left open one line
  earlier. Wrap the decode and re-raise as `PersistError`:

  ```
  try:
      raw = target.read_bytes().decode("utf-8")
  except ValueError as exc:                        # UnicodeDecodeError is a ValueError
      raise PersistError(f"{target} is not valid UTF-8: {exc}") from exc
  ```
- `_atomic_write` does `target.parent.mkdir(parents=True, exist_ok=True)` — `.icoder/` may not
  exist, since `_discover_layers` only picks up files that exist and `emit_schema` bails when
  `.icoder` is not a directory — then `tempfile.mkstemp(dir=target.parent)`, writes with
  `encoding="utf-8", newline=""` (so the newlines built above survive on win32), and `os.replace`.
  On any exception the temp file is unlinked before re-raising.
- New-file skeleton is `"{\n}\n"`; `_insert_section` then adds the list. One code path for
  "brand-new file" and "existing file missing the key".
- `write_rule` returns `None` and raises `OSError` on an unwritable target, and `PersistError`
  (an `OSError` subclass) when the existing file is not valid UTF-8, is unparseable JSONC, has a
  non-object root, holds a non-list value under `allow` / `ask` / `deny`, or when the move branch
  cannot locate the array or the item it is asked to remove.
  One failure type, so step 5's single `except OSError` branch degrades to a session grant and
  still calls `resolve_pending` — an unparseable local file must never wedge the turn. Nothing
  is written in either case: both raises happen before `_atomic_write`.

Matcher shapes in v1 are whole-matcher (non-arg) only — `mcp__server__tool`, `mcp__server__*`,
`@group`. The insert is matcher-string-agnostic, so nothing here enumerates them.

## TDD — tests first

`tests/icoder/test_permissions_persist.py`, **unmarked** (no `pytestmark`), plain `tmp_path` unit
tests over JSONC fixtures. Never an in-repo fixture file: the MCP file tools refuse gitignored
paths, and `.icoder/settings.local.json` is intended to be gitignored.

| Test | Fixture / assert |
|---|---|
| `test_creates_file_and_directory_when_absent` | no `.icoder/`; after `write_rule` the dir and file exist and `load_permission_config(tmp_path)` yields an `ALWAYS` rule for the tool |
| `test_inserts_into_an_empty_array` | `{"allow": []}` |
| `test_inserts_into_a_non_empty_array_keeping_existing_order` | the pre-existing matcher is still present and still first |
| `test_preserves_line_and_block_comments` | both a `//` line and a `/* ... */` block survive verbatim |
| `test_double_slash_inside_a_string_is_not_a_comment` | a `"https://example.com//x"` value survives intact |
| `test_escaped_quote_inside_a_string` | a value containing `\"` does not desynchronise the scanner |
| `test_trailing_comma_is_tolerated` | `{"allow": ["a",],}` |
| `test_absent_key_gets_a_scaffold` | file holds only `"ask"`; after writing `allow`, both keys parse and `ask` is byte-identical |
| `test_crlf_newlines_are_preserved` | written with CRLF; afterwards the bytes contain `\r\n` and no lone `\n` |
| `test_indentation_matches_existing_items` | a 4-space-indented array stays 4-space |
| `test_matcher_in_another_list_is_moved_not_duplicated` | matcher in `ask`; write to `allow` → absent from `ask`, present in `allow`, and appears exactly once in the whole file |
| `test_already_present_is_a_no_op` | file bytes unchanged |
| `test_no_temp_file_is_left_behind` | `.icoder/` holds no `*.tmp` afterwards |
| `test_default_mode_value_is_not_mistaken_for_the_key` | **parametrised** over `{"defaultMode": "allow"}` (no `allow` array) and `{"defaultMode": "allow", "allow": ["x"]}`; after writing, the text contains exactly **one** top-level `"allow":` key, `defaultMode` is still `"allow"`, and `load_permission_config(tmp_path)` yields `ALWAYS` for the tool — i.e. the file still passes schema validation |
| `test_invalid_utf8_raises_persist_error` | write raw bytes `b'{"allow": ["\xff\xfe"]}'` (invalid UTF-8) to `settings.local.json`; `pytest.raises(PersistError)` — assert the type explicitly, since the bug this pins is a `UnicodeDecodeError`/`ValueError` from `_read` that would escape the caller's `except OSError` — and the file bytes are unchanged |
| `test_malformed_jsonc_raises_persist_error` | file holds `{"allow": [` ; `pytest.raises(PersistError)` and the file bytes are unchanged. Also assert `issubclass(PersistError, OSError)`, which is what makes step 5's degrade branch cover it |
| `test_non_object_root_raises_persist_error` | file holds `["mcp__srv__x"]`; `pytest.raises(PersistError)` and the file bytes are unchanged |
| `test_unlocatable_move_item_raises_persist_error` | file holds a **duplicate top-level key**, `{"ask": [], "ask": ["mcp__a__b"]}` (valid JSON — `json.loads` keeps the second, `_find_section_array` returns the first, empty array); write `mcp__a__b` to `allow`; `pytest.raises(PersistError)` — assert the type explicitly, since the bug this pins is a `TypeError` from `_remove_item(text, None)` that would escape the caller's `except OSError` — and the file bytes are unchanged |
| `test_non_list_section_raises_persist_error` | **parametrised** over `{"allow": "mcp__a__b"}` (writing to `allow`) and `{"ask": "mcp__a__b"}` (writing to `allow`, so the move branch is the one that would blow up); `pytest.raises(PersistError)` — assert the type explicitly, since the bug this pins is a `TypeError` from the `*None` unpack that would escape the caller's `except OSError` — and the file bytes are unchanged |

Give the module a `_reload(tmp_path, tool)` helper that runs `load_permission_config` + `resolve`
so most cases end with a real round-trip rather than a string assertion.

## Acceptance

- All writer tests pass in the fast (unmarked) selection.
- `lint-imports` passes with the new module registered.
- pylint / mypy(strict) / ruff-docstrings clean.
- `persist.py` well under the 750-line gate (expect ~180 lines).

## Commit

`feat(permissions): add comment-preserving JSONC rule write-back (#1046)`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Steps 1–3 must be committed first.
>
> Implement step 4 only: create `src/mcp_coder/icoder/permissions/persist.py` exactly as specified
> under WHAT / HOW / ALGORITHM / DATA, and register it in `.importlinter`'s
> `permissions_leaf_isolation` `source_modules` (not in `permissions_core_purity`). Do not touch
> `ui/stream_view.py` — wiring is step 5.
>
> Work TDD: first write `tests/icoder/test_permissions_persist.py` with the nineteen cases from
> the table (unmarked, `tmp_path` only, never an in-repo fixture file), watch them fail, then write
> the module.
>
> Reuse `loader._strip_jsonc` only as a parser via `json.loads(_strip_jsonc(text))`, wrapped so a
> `ValueError`, a non-object root and a non-list `allow`/`ask`/`deny` value all become
> `PersistError`. Wrap `_read`'s `decode("utf-8")` the same way — `UnicodeDecodeError` is a
> `ValueError`, and it happens before every other guard.
> `PersistError` must be the module's only failure type: anything else escapes the
> caller's `except OSError` and wedges the turn. That also covers the move branch — route it
> through `_locate_item`, which turns a `None` from `_find_section_array` or `_find_item` into a
> `PersistError` instead of letting it reach a `*` unpack or `_remove_item` as a `TypeError`.
>
> Author `_scan` as the locator — do not try to derive offsets from `_strip_jsonc`. Do not add a full JSON round-trip: comments
> must survive. Re-run `_scan` after each text mutation instead of adjusting offsets.
>
> In `_find_section_array`, the `:` + `[` check after a depth-1 string is a guard that must
> continue the scan on failure, never return `None` — `defaultMode`'s value is legitimately
> `"allow"` / `"ask"` / `"deny"`.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff, lint-imports and the fast unit test
> selection. Make exactly one commit when everything passes.
