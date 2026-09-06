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

## ALGORITHM — invariants, not pseudo-code

The bodies are deliberately left to the implementer; **the test table below is the
specification**. What the implementation must satisfy:

1. **`_scan` is the only primitive.** One pass over the text yielding `code` / `string` /
   `comment` spans as offsets into the *original* text; everything else slices that text. String
   walking honours `\` escapes; both `//` (to end of line) and `/* … */` comments are recognised.
   Bracket depth is counted over **code spans only**, so a bracket inside a string or a comment
   can never move it.

2. **A depth-1 string equal to the section name is the key only when followed by `:` then `[`**
   (skipping whitespace over code chars). **On failure the scan continues — it must not return
   `None`.** `defaultMode` is a top-level key whose schema enum is exactly
   `"allow" | "ask" | "deny"` (`loader.py::build_settings_schema`), so
   `{"defaultMode": "allow", "allow": [...]}` legitimately puts a depth-1 string `"allow"` in the
   text that is a *value*. Bailing there makes `write_rule` emit a second top-level `"allow"` key
   — a file that fails schema validation and degrades the whole config fail-closed.

3. **Insert immediately after the opening `[`**, so existing items, their comments and their
   indentation are never touched and the diff is one added line. Indent like the first existing
   item's line, else the `[` line's indent + two spaces; an inline (newline-free) array stays
   inline. When the key is absent, `_insert_section` adds a fresh `"<section>": [ … ]` block
   after the root `{`, one item per line (design §8.2).

4. **Re-run `_scan` after every mutation; never adjust offsets.** A settings file is small and
   this removes a whole class of off-by-one bugs.

5. **`PersistError` is the module's only failure type, and nothing is written when it raises** —
   every raise happens before `_atomic_write`. It must cover *all* of: a non-UTF-8 file, an
   unparseable JSONC body, a non-object root, a non-list value under `allow` / `ask` / `deny`,
   and **both** `None` results on the move branch (`_find_section_array` and `_find_item`, routed
   through `_locate_item` so neither reaches a `*` unpack or `_remove_item`). Each of those
   otherwise surfaces as a `ValueError` or a `TypeError`, which escapes step 5's single
   `except OSError`, skips `resolve_pending` and wedges the turn. Schema validation is not
   available here — the writer must not import the loader's jsonschema path for one check.

6. **`write_rule` is idempotent and moves rather than duplicates.** Matcher already in the target
   section: return without touching the file (no mtime change). Matcher in one of the other two
   sections: `_remove_item` deletes its span plus one adjacent comma — dropping the whole line
   when nothing else remains on it — before the insert.

## DATA

- `_read(target) -> tuple[str, str]` uses `target.read_bytes().decode("utf-8")`, **not**
  `read_text()`, which applies universal-newline translation and would silently convert CRLF to
  LF. Newline style is one check: `"\r\n" if "\r\n" in raw else "\n"`.
  The decode is inside invariant 5 — `UnicodeDecodeError` is a `ValueError`, and it happens
  before every other guard, so wrap it and re-raise as `PersistError`.
- `_atomic_write` does `target.parent.mkdir(parents=True, exist_ok=True)` — `.icoder/` may not
  exist, since `_discover_layers` only picks up files that exist and `emit_schema` bails when
  `.icoder` is not a directory — then `tempfile.mkstemp(dir=target.parent)`, writes with
  `encoding="utf-8", newline=""` (so the newlines built above survive on win32), and `os.replace`.
  On any exception the temp file is unlinked before re-raising.
- New-file skeleton is `"{\n}\n"`; `_insert_section` then adds the list. One code path for
  "brand-new file" and "existing file missing the key".
- `write_rule` returns `None`, raises a plain `OSError` on an unwritable target, and otherwise
  raises `PersistError` per invariant 5 — one failure type, so step 5's single `except OSError`
  branch degrades to a session grant and still calls `resolve_pending`.

Matcher shapes in v1 are whole-matcher (non-arg) only — `mcp__server__tool`, `mcp__server__*`,
`@group`. The insert is matcher-string-agnostic, so nothing here enumerates them.

## TDD — tests first

`tests/icoder/test_permissions_persist.py`, **unmarked** (no `pytestmark`), plain `tmp_path` unit
tests over JSONC fixtures. Never an in-repo fixture file: the MCP file tools refuse gitignored
paths, and `.icoder/settings.local.json` is intended to be gitignored.

| Test | Fixture / assert |
|---|---|
| `test_creates_file_and_directory_when_absent` | no `.icoder/`; after `write_rule` the dir and file exist; the produced text parses with **plain `json.loads`** — not through `_strip_jsonc` — so a scaffold written into the `"{\n}\n"` skeleton cannot carry a trailing comma; and `_reload(...)` returns `policy is Policy.ALWAYS` **and** `source == Layer("local")` |
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
| `test_no_temp_file_is_left_behind` | afterwards `.icoder/` holds exactly one entry, `settings.local.json`. Do **not** glob for `*.tmp`: `mkstemp(dir=...)` uses the default empty suffix and a `tmp` *prefix*, so that glob matches nothing whether or not a temp file leaked |
| `test_default_mode_value_is_not_mistaken_for_the_key` | **parametrised** over `{"defaultMode": "allow"}` (no `allow` array) and `{"defaultMode": "allow", "allow": ["x"]}`; after writing, the text contains exactly **one** top-level `"allow":` key, `defaultMode` is still `"allow"`, and `_reload(...)` returns `policy is Policy.ALWAYS` **and** `source == Layer("local")` — i.e. the file still passes schema validation *and* the new rule is what decided |
| `test_invalid_utf8_raises_persist_error` | write raw bytes `b'{"allow": ["\xff\xfe"]}'` (invalid UTF-8) to `settings.local.json`; `pytest.raises(PersistError)` — assert the type explicitly, since the bug this pins is a `UnicodeDecodeError`/`ValueError` from `_read` that would escape the caller's `except OSError` — and the file bytes are unchanged |
| `test_malformed_jsonc_raises_persist_error` | file holds `{"allow": [` ; `pytest.raises(PersistError)` and the file bytes are unchanged. Also assert `issubclass(PersistError, OSError)`, which is what makes step 5's degrade branch cover it |
| `test_non_object_root_raises_persist_error` | file holds `["mcp__srv__x"]`; `pytest.raises(PersistError)` and the file bytes are unchanged |
| `test_unlocatable_move_item_raises_persist_error` | file holds a **duplicate top-level key**, `{"ask": [], "ask": ["mcp__a__b"]}` (valid JSON — `json.loads` keeps the second, `_find_section_array` returns the first, empty array); write `mcp__a__b` to `allow`; `pytest.raises(PersistError)` — assert the type explicitly, since the bug this pins is a `TypeError` from `_remove_item(text, None)` that would escape the caller's `except OSError` — and the file bytes are unchanged |
| `test_non_list_section_raises_persist_error` | **parametrised** over `{"allow": "mcp__a__b"}` (writing to `allow`) and `{"ask": "mcp__a__b"}` (writing to `allow`, so the move branch is the one that would blow up); `pytest.raises(PersistError)` — assert the type explicitly, since the bug this pins is a `TypeError` from the `*None` unpack that would escape the caller's `except OSError` — and the file bytes are unchanged |

Give the module a `_reload(tmp_path, tool, monkeypatch)` helper that runs `load_permission_config`
+ `resolve` so most cases end with a real round-trip rather than a string assertion.

**Callers must assert `decision.source == Layer("local")`, not merely
`decision.policy is Policy.ALWAYS`.** `_reload` already returns a `Decision`, and `resolver.py:191`
returns `Decision(Policy.ALWAYS, Default(), None, None)` whenever *no* rule matches — so a
policy-only assertion passes identically when `write_rule` wrote nothing at all, which makes the
round-trip unfalsifiable. Checking the source is what pins that the reloaded `local` rule is the
thing that decided. Rows whose disk state deliberately produces a different layer or policy say so
explicitly.

**The helper must isolate the user layer first.** `_discover_layers` reads
`get_user_app_data_dir("mcp_coder") / ".icoder" / "settings.json"` — a real machine path, not
anything under `tmp_path`. A developer's or CI runner's own user-layer file therefore joins every
`load_permission_config(tmp_path)` call: a user-level `ask`/`deny` for the tool changes the
resolved policy, and a malformed user file sets `degraded=True`, which drives *every* tool to
`AFTER_APPROVAL`. Both silently flip these assertions on one machine and not another. Do exactly
what `tests/icoder/test_permissions_loader_layers.py:460`'s `_empty_user_dir` does, inside
`_reload`, so every row routed through it is covered:

```python
def _reload(tmp_path: Path, tool: str, monkeypatch: pytest.MonkeyPatch) -> Decision:
    user_root = tmp_path / "user"
    user_root.mkdir(exist_ok=True)
    monkeypatch.setattr(
        "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
        lambda _app: user_root,
    )
    return resolve(tool, {}, None, load_permission_config(tmp_path))
```

Any test in this file that calls `load_permission_config(tmp_path)` directly rather than through
`_reload` must apply the same monkeypatch.

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
> Implement step 4 only: create `src/mcp_coder/icoder/permissions/persist.py` with the signatures
> under WHAT, satisfying every invariant under ALGORITHM and every bullet under DATA, and register
> it in `.importlinter`'s `permissions_leaf_isolation` `source_modules` (not in
> `permissions_core_purity`). Do not touch `ui/stream_view.py` — wiring is step 5.
>
> The ALGORITHM section is deliberately invariants, not pseudo-code. The nineteen tests are the
> specification — write `tests/icoder/test_permissions_persist.py` first (unmarked, `tmp_path`
> only, never an in-repo fixture file), watch them fail, then write the module however you like so
> long as the invariants hold.
>
> Reuse `loader._strip_jsonc` only as a parser via `json.loads(_strip_jsonc(text))`; author `_scan`
> as the locator, and do not add a full JSON round-trip — comments must survive.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff, lint-imports and the fast unit test
> selection. Make exactly one commit when everything passes.
