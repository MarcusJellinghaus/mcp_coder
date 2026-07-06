# Step 2 — Extract `verify_formatting.py`

> Read [`summary.md`](./summary.md) first. This step is one commit / one PR.
> Pure **move** refactor — no logic changes, imports only.

## Goal

Move the formatting primitives **and the constant maps they use** into a new pure
leaf module. `verify.py` drops to ~620 lines → **remove its `.large-files-allowlist`
entry in this step**.

## WHERE

- **New:** `src/mcp_coder/cli/commands/verify_formatting.py`
- **Modified:** `src/mcp_coder/cli/commands/verify.py`, `.large-files-allowlist`
- **Function importers** (`move_symbol` auto-rewrites): `test_verify_alignment.py`,
  `test_verify_format_mcp_section.py`, `test_verify_format_pad.py`,
  `test_verify_format_section_basic.py`, `test_verify_tools_exposed.py`,
  `test_verify.py`, `test_verify_orchestration.py`, `conftest.py`
- **Constant importers** (manual repoint — see HOW): `conftest.py`, `test_verify.py`,
  `test_verify_command.py`, `test_verify_format_pad.py`,
  `test_verify_format_section_basic.py` (incl. in-function imports at lines ~219/282),
  `test_verify_tools_exposed.py`, `test_verify_orchestration.py` (in-function import
  at line ~1501)

## WHAT (symbols to move — verbatim)

**Functions:** `_format_row_prefix`, `_format_row`, `_pad`, `_looks_like_key`,
`_format_section`, `_format_mcp_section`, `_format_claude_mcp_section`,
`_format_tools_exposed_section`

**Constants (move manually only if the `move_symbol` dry-run leaves them behind — see HOW/ALGORITHM):**
`STATUS_SYMBOLS`, `_MARKER_SLOT_WIDTH`, `_LABEL_WIDTH`, `_KEY_REGEX`,
`_VALUE_COLUMN_INDENT`, `_LABEL_MAP`, `_BRANCH_PROTECTION_CHILDREN`

> `move_symbol` claims to move top-level functions, classes, **or variables**, so it
> may relocate these constants for you. Do **not** assume either way — the dry-run in
> the ALGORITHM below is the source of truth. Only perform the manual constant move if
> the dry-run shows they were left in `verify.py`.

## HOW (integration)

**Required order inside `verify_formatting.py`** (import-time dependencies):

```
imports: import keyword, re; from typing import Any
STATUS_SYMBOLS
_MARKER_SLOT_WIDTH          # = max(len(v) for v in STATUS_SYMBOLS.values())
_LABEL_WIDTH
_format_row_prefix          # uses _LABEL_WIDTH, _MARKER_SLOT_WIDTH
_format_row                 # uses _format_row_prefix
_VALUE_COLUMN_INDENT        # = len(_format_row_prefix("", "", indent=2))  <-- MUST follow _format_row_prefix
_pad
_KEY_REGEX
_looks_like_key             # uses _KEY_REGEX, keyword
_LABEL_MAP
_BRANCH_PROTECTION_CHILDREN
_format_section             # uses _pad, _LABEL_MAP, _BRANCH_PROTECTION_CHILDREN, _format_row, _VALUE_COLUMN_INDENT
_format_mcp_section         # uses _pad, _format_row, _format_row_prefix
_format_claude_mcp_section  # uses _pad, _format_row
_format_tools_exposed_section
```

**`verify.py` after the move** still uses the following from the moved set, so it must
import them back (one-directional edge `verify.py -> verify_formatting`):

```python
from .verify_formatting import (
    STATUS_SYMBOLS,
    _LABEL_WIDTH,
    _VALUE_COLUMN_INDENT,
    _format_claude_mcp_section,
    _format_mcp_section,
    _format_row,
    _format_section,
    _format_tools_exposed_section,
    _looks_like_key,
    _pad,
)
```
(`_format_row_prefix`, `_LABEL_MAP`, `_KEY_REGEX`, `_MARKER_SLOT_WIDTH`,
`_BRANCH_PROTECTION_CHILDREN` are used only by the moved functions, so `verify.py`
does not import them.)

- No `.importlinter` / `tach.toml` change (leaf, one-directional, no cycle).

## ALGORITHM (execution)

```
1. move_symbol(verify.py, [<8 functions>], verify_formatting.py, dry_run=True) -> review.
   # OBSERVE two things in the dry-run:
   #  (a) Whether the 7 module-level constants were relocated to verify_formatting or
   #      left behind in verify.py. This decides whether step 3 (manual move) is needed.
   #  (b) Whether move_symbol added a `from .verify import <consts>` back-edge into
   #      verify_formatting (a temporary back-edge to clean up in steps 3-5 below).
2. move_symbol(... dry_run=False)
3. ONLY IF the dry-run showed the constants stayed in verify.py: manually cut the 7
   constant definitions from verify.py and paste them into verify_formatting.py in the
   REQUIRED ORDER above. If the dry-run already relocated them, skip the cut/paste but
   still verify they landed in the REQUIRED ORDER (fix ordering if not) — in particular
   `_VALUE_COLUMN_INDENT` MUST follow `_format_row_prefix`.
4. Delete any auto-added `from .verify import <constants>` line in verify_formatting.py.
5. Reconcile imports: every remaining `from ...commands.verify import <X>` where X is
   one of the 7 constants -> repoint to `...commands.verify_formatting`
   (conftest.py, test_verify*.py, incl. the two in-function imports). mypy/pytest flag stragglers.
6. Ensure verify.py has the `from .verify_formatting import (...)` block shown above.
7. Remove `src/mcp_coder/cli/commands/verify.py` from .large-files-allowlist.
8. Run all checks + git-tool compact-diff + check_file_size(max_lines=750).
```

> **Do not run quality checks mid-sequence.** The steps above pass through
> intermediate broken states — split imports, a temporary `verify_formatting -> verify`
> back-edge from `move_symbol`, and un-repointed straggler importers — that will **not**
> import cleanly. Run format / lint-imports / pytest / pylint / mypy / tach only once the
> **entire** ALGORITHM sequence is complete. This remains a single step / single commit.

## DATA (unchanged contracts)

Row/section formatters return `str` (or `list[str]` lines / `tuple[list[str], bool|None]`
for `_format_tools_exposed_section`) exactly as before. Constants keep their types:
`STATUS_SYMBOLS: dict[str,str]`, `_LABEL_MAP: dict[str,str]`,
`_BRANCH_PROTECTION_CHILDREN: frozenset[str]`, width ints, `_KEY_REGEX: re.Pattern`.

## Test phase (TDD-equivalent)

No new test logic. The formatting-focused companion tests already cover these
functions/constants; confirm the suite stays green after repointing imports.

## Done when

- [x] `verify_formatting.py` created with functions + constants in the required order.
- [x] `verify.py` imports the needed subset back; no `verify_formatting -> verify` edge.
- [x] All function + constant importers repoint correctly (no `ImportError`, mypy clean).
- [x] `verify.py` removed from `.large-files-allowlist`; `check_file_size` passes.
- [x] `compact-diff` shows only import / new-file churn.
- [x] format + lint-imports + pytest + pylint + mypy pass; `tach check` passes (tach
      unavailable in this environment; import-linter's 19 contracts all KEPT cover the
      leaf/no-cycle boundary, and the design requires no contract change).
