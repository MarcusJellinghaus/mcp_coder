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

class Span(NamedTuple):
    kind: str      # "code" | "string" | "comment"
    start: int
    end: int

def _scan(text: str) -> list[Span]: ...
def _find_section_array(text, spans, section) -> tuple[int, int] | None: ...
def _find_item(text, spans, open_i, close_i, matcher) -> Span | None: ...
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
        walk code chars after the span: expect ':' then '[' -> open_i
        keep walking code chars counting '[' / ']' -> matching close_i
        return (open_i, close_i)
return None
```

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
data = json.loads(_strip_jsonc(text))
if matcher in data.get(section, []): return      # idempotent: no write, no mtime change
for other in ("allow","ask","deny") if other != section and matcher in data.get(other, []):
    text = _remove_item(text, _find_item(text, _scan(text), *_find_section_array(...), matcher))
arr = _find_section_array(text, _scan(text), section)
text = _insert_item(text, *arr, matcher, newline) if arr else _insert_section(text, ..., newline)
_atomic_write(target, text)
```

Re-run `_scan` after every mutation rather than adjusting offsets. A settings file is small and
this removes a whole class of off-by-one bugs.

## DATA

- `_read(target) -> tuple[str, str]` uses `target.read_bytes().decode("utf-8")`, **not**
  `read_text()`, which applies universal-newline translation and would silently convert CRLF to
  LF. Newline style is one check: `"\r\n" if "\r\n" in raw else "\n"`.
- `_atomic_write` does `target.parent.mkdir(parents=True, exist_ok=True)` — `.icoder/` may not
  exist, since `_discover_layers` only picks up files that exist and `emit_schema` bails when
  `.icoder` is not a directory — then `tempfile.mkstemp(dir=target.parent)`, writes with
  `encoding="utf-8", newline=""` (so the newlines built above survive on win32), and `os.replace`.
  On any exception the temp file is unlinked before re-raising.
- New-file skeleton is `"{\n}\n"`; `_insert_section` then adds the list. One code path for
  "brand-new file" and "existing file missing the key".
- `write_rule` returns `None` and raises `OSError` on an unwritable target (step 5 handles it).

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
> Work TDD: first write `tests/icoder/test_permissions_persist.py` with the thirteen cases from
> the table (unmarked, `tmp_path` only, never an in-repo fixture file), watch them fail, then write
> the module.
>
> Reuse `loader._strip_jsonc` only as a parser via `json.loads(_strip_jsonc(text))`. Author `_scan`
> as the locator — do not try to derive offsets from `_strip_jsonc`. Do not add a full JSON
> round-trip: comments must survive. Re-run `_scan` after each text mutation instead of adjusting
> offsets.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff, lint-imports and the fast unit test
> selection. Make exactly one commit when everything passes.
