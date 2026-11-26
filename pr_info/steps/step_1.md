# Step 1 — Shim `mcp_coder.utils.verify_render`; delete the local render primitives

Read [summary.md](summary.md) first. One commit.

## LLM prompt

> Implement step 1 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_1.md`.
> Write the shim test first, then the shim, then switch every user of the local primitives
> to the shim and delete the local copies and the tests that moved upstream. Output of
> `mcp-coder verify` must not change. Run pylint, pytest (`-n auto`, fast unit markers),
> mypy, ruff, lint-imports, tach, vulture, deptry; format; commit.

## Precondition

`mcp_coder_utils.verify_render` exports `STATUS_SYMBOLS`, `Row`, `Line`, `SectionBuilder`,
`hint_row`, `render_rows` (check with `get_library_source`). If not, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE

- New: `src/mcp_coder/utils/verify_render.py`, `tests/utils/test_verify_render_shim.py`
- Delete: `src/mcp_coder/cli/commands/verify_render.py`, `tests/cli/commands/test_verify_format_pad.py`
- Modify (src): `cli/commands/verify_formatting.py`, `verify.py`, `verify_sections.py`,
  `verify_setup.py`, `verify_toolkit_rows.py`, `verify_project_keys.py`
- Modify (tests): `tests/cli/commands/conftest.py`, `test_verify_render.py`,
  `test_verify_label_map.py`, every `tests/cli/commands/test_verify*.py` importing a deleted
  name, `tests/llm/providers/langchain/test_langchain_contract_rows.py`,
  `tests/utils/test_no_toolkit_error.py`
- Modify (config/docs): `.importlinter`, `.claude/CLAUDE.md`, `docs/architecture/architecture.md`

## WHAT

### `src/mcp_coder/utils/verify_render.py` (new)

```python
"""Shim for mcp-coder-utils' status-check rendering primitives."""

from mcp_coder_utils.verify_render import (
    STATUS_SYMBOLS, Line, Row, SectionBuilder, hint_row, render_rows,
)

__all__ = ["STATUS_SYMBOLS", "Line", "Row", "SectionBuilder", "hint_row", "render_rows"]
```

### `verify_formatting.py`

- Delete: `STATUS_SYMBOLS`, `_MARKER_SLOT_WIDTH`, `_LABEL_WIDTH`, `Row`, `Line`, `_hint`,
  `_section_label_width`, `_format_row_prefix`, `_format_row`, `_pad`.
- Add `from ...utils.verify_render import Line, Row, hint_row`; rename `_hint(` → `hint_row(`.
- Everything else stays in this step (`_LABEL_MAP`, `_format_section`, MCP / Claude MCP /
  tools-exposed formatters, `_looks_like_key`). Update the module docstring (no longer holds
  the primitives).

### Other src users

Import `STATUS_SYMBOLS`, `Row`, `Line`, `SectionBuilder`, `hint_row` from
`...utils.verify_render` (`verify.py`, `verify_sections.py`, `verify_setup.py`,
`verify_toolkit_rows.py`, `verify_project_keys.py`). `verify_sections._hint(` → `hint_row(`.
No module keeps a second copy or re-exports these names for others.

## HOW

- `.importlinter` contract `mcp_coder_utils_isolation`: add
  `mcp_coder.utils.verify_render -> mcp_coder_utils` to `ignore_imports`; header comment
  becomes "only be imported by the shim files listed in `ignore_imports`" (6 today).
- `.claude/CLAUDE.md` "Shared Libraries": table lists all 6 shims —
  add rows `mcp_coder.utils.toolkit`, `mcp_coder.utils.user_app_data` (check their upstream
  modules in the files) and `mcp_coder.utils.verify_render` → `mcp_coder_utils.verify_render`
  (`STATUS_SYMBOLS`, `Row`, `Line`, `SectionBuilder`, `hint_row`, `render_rows`); fix the
  "Three shim modules" sentence.
- `docs/architecture/architecture.md` shims row: add `utils/verify_render` (mcp-coder-utils
  render primitives) and the other `utils` shims of mcp-coder-utils.

## Tests (write first)

`tests/utils/test_verify_render_shim.py`:

```python
import mcp_coder_utils.verify_render as upstream
from mcp_coder.utils import verify_render as shim

@pytest.mark.parametrize("name", upstream.__all__)
def test_shim_reexports_upstream_object(name): assert getattr(shim, name) is getattr(upstream, name)
```

(The identity test also proves the shim's `Row` is upstream's `Row`.)

(`tests` may import `mcp_coder_utils`; the isolation contract covers `mcp_coder` only.)

Test updates:

- `tests/cli/commands/conftest.py`: import `STATUS_SYMBOLS`, `Line`, `Row`, `SectionBuilder`,
  `render_rows` from `mcp_coder.utils.verify_render`; replace `_LABEL_WIDTH` / `_MARKER_SLOT_WIDTH`
  with module constants `_LABEL_WIDTH = 22`, `_MARKER_SLOT_WIDTH = 6` (comment: the layout
  of mcp-coder-utils' renderer; value column 32); `_render` uses `render_rows`. Add

  ```python
  def _format_row(label: str, marker: str, value: str, *, indent: int = 2) -> str:
      """One row rendered on its own, as the renderer prints it."""
      return render_rows([Row(label, marker, value, indent)])[0]
  ```

  Tests importing `_format_row`, `_LABEL_WIDTH`, `_MARKER_SLOT_WIDTH` from
  `verify_formatting` import them from `.conftest` instead.
- Delete `tests/cli/commands/test_verify_format_pad.py`.
- `test_verify_render.py`: delete `TestRenderRows`, `TestSectionBuilder`,
  `test_assert_section_aligned_rejects_misaligned_values`,
  `test_github_permissions_section_aligned_with_token_hint`; keep
  `TestSectionHelpersThroughBuilder`, fix its imports (shim + `.conftest`), drop unused ones.
- `test_verify_label_map.py`: `_LABEL_WIDTH` → literal 22 (local constant).
- `tests/llm/providers/langchain/test_langchain_contract_rows.py`: `_LABEL_WIDTH` → local
  constant 22, `_render_rows` → `render_rows` from `mcp_coder.utils.verify_render`
  (do not import from `tests.cli` — `test_module_independence` contract).
- `tests/utils/test_no_toolkit_error.py`: `SectionBuilder` from the shim.
- Every other `tests/**` import of a deleted name: search for
  `verify_render import|_LABEL_WIDTH|_MARKER_SLOT_WIDTH|_render_rows|_format_row|_hint\b|_pad\b|STATUS_SYMBOLS|import .*\bRow\b`
  and switch to the shim / `.conftest`. Exact-text assertions stay unchanged.

## ALGORITHM

None — re-export and import swaps.

## DATA

Unchanged: `Row(label, marker, value, indent=2, wrap=False)`, `Line = Row | str`.
