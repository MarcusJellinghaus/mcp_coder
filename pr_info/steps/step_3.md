# Step 3 — Split `test_verify_orchestration.py` by test class

> Read [`summary.md`](./summary.md) first. This step is one commit / one PR.
> **Assumes Steps 1 & 2 are merged** (imports reference `verify_formatting`).
> Test-only reorganization — no source change, no logic change.

## Goal

Split the ~1868-line `test_verify_orchestration.py` into concern-specific files, each
< 750 lines, by existing test class. Shared module-level helpers move into the existing
`conftest.py` (the directory's established pattern — it already exports
`_assert_value_at_column`, `_expected_value_column`, `_make_verify_mocks`). Then
**remove `test_verify_orchestration.py` from `.large-files-allowlist`**.

Do **not** use `move_symbol` here — test modules have no importers, so it adds no value
and complicates class-with-helper moves. Use plain `save_file` / `edit_file` /
`append_file`.

## WHERE

- **Modified:** `tests/cli/commands/conftest.py` (gains shared helpers),
  `tests/cli/commands/test_verify_orchestration.py` (reduced to one class group),
  `.large-files-allowlist`
- **New:** `tests/cli/commands/test_verify_mcp_orchestration.py`,
  `tests/cli/commands/test_verify_sections_orchestration.py`
  (filenames at implementer's discretion — only constraint: split by concern, each < 750)

## WHAT — helpers to move into `conftest.py`

Module-level helpers currently at the top of `test_verify_orchestration.py`
(lines ~26–116) plus the two patch-target constants:

```
_make_args, _minimal_llm_response, _claude_ok, _langchain_ok, _langchain_fail,
_mlflow_ok, _mlflow_not_installed, _mlflow_enabled_broken, _github_ok_default
_LC_VERIFY = "mcp_coder.llm.providers.langchain.verification"
_VERIFY    = "mcp_coder.cli.commands.verify"
```

Move verbatim. (Do not attempt to dedupe against the inline copies inside
`_make_verify_mocks` — that would be a logic change; out of scope.)

## WHAT — class → file assignment (recommended)

| File | Classes | ~lines |
|------|---------|--------|
| `test_verify_orchestration.py` (keep name) | `TestVerifyOrchestration`, `TestVerifyTestPromptFailure` | ~625 |
| `test_verify_mcp_orchestration.py` (new) | `TestVerifyMcpAllProviders`, `TestMcpConfigWarnings`, `TestMcpConfigWarningsDynamicWidth` | ~635 |
| `test_verify_sections_orchestration.py` (new) | `TestMcpConfigValidityRow`, `TestDropUnexpandedFilter`, `TestConditionalClaudeDisplay`, `TestInstallSummaryBlock`, `TestVerifyGitHubOrchestration`, `TestGitWiring` | ~570 |

All three land comfortably < 750. If a real count exceeds 750, shift one class to
another file — concern grouping is a guide, the hard rule is the line limit.

## HOW (integration)

Each split file gets:
- Its own stdlib / pytest / `unittest.mock` imports (copy the subset it uses).
- `from mcp_coder.cli.commands.verify import ...` for symbols that stayed in `verify.py`
  (`execute_verify`, `_validate_mcp_config`, `_DropUnexpandedWarnings`).
- `from mcp_coder.cli.commands.verify_formatting import _format_mcp_section` where used
  (moved there in Step 2; also the in-function `_LABEL_WIDTH` / `_MARKER_SLOT_WIDTH`).
- `from mcp_coder.utils.mcp_verification import ClaudeMCPStatus` where used.
- Shared helpers via `from .conftest import _make_args, _claude_ok, ...` (mirrors the
  existing `from .conftest import _assert_value_at_column` pattern).

Rely on pylint (unused-import) + mypy + pytest to confirm each file imports exactly
what it needs — no manual per-symbol accounting required.

## ALGORITHM (execution)

```
1. append the shared helpers + _LC_VERIFY/_VERIFY to conftest.py (verbatim).
2. save_file the two NEW files: imports + their assigned class bodies (verbatim).
3. edit_file test_verify_orchestration.py: drop the moved helpers and the classes
   now living elsewhere; keep only its assigned group + needed imports (now sourced
   from conftest for helpers).
4. Remove tests/cli/commands/test_verify_orchestration.py from .large-files-allowlist.
5. Run pytest (collect count must equal pre-split total) + all checks + check_file_size.
```

## DATA

No runtime data structures change. Test collection count before == after (no tests
added/removed/renamed). `check_file_size(max_lines=750)` reports zero offenders for
these files.

## Test phase (TDD-equivalent)

The tests themselves are the artifact. Verify by running the full (fast) suite and
confirming the same set of tests passes, just distributed across three files.

## Done when

- [x] Shared helpers live in `conftest.py`; each split file imports them from there.
- [x] Three files, each < 750 lines; no class duplicated or dropped.
- [x] `test_verify_orchestration.py` removed from `.large-files-allowlist`;
      `check_file_size` passes (and no stale entry remains for it).
- [x] pytest collection count unchanged; format + lint-imports + pytest + pylint +
      mypy pass; `tach check` passes.
