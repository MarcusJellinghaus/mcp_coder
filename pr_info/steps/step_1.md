# Step 1 — Install output through logging

## LLM prompt
> Read `pr_info/steps/summary.md` (section "Architectural / design changes" §1) and this
> file. Implement step 1 only: replace every `print()` in `src/mcp_coder/install/` with
> logging and migrate the tests that read install output from `capsys` to `caplog`.
> Update the tests first, then the code. Run ruff check, pylint, mypy and the fast unit
> tests (CLAUDE.md), format, and make one commit.

## WHERE
- `src/mcp_coder/install/_env.py`
- `src/mcp_coder/install/_phases.py`
- `src/mcp_coder/install/__init__.py`
- `tests/install/test_install_phases.py`
- `tests/install/test_install_post_checks.py`

## WHAT
No new functions. In each of the three source modules add:

```python
import logging
from ..utils.log_utils import OUTPUT

logger = logging.getLogger(__name__)
```

(`__init__.py`: `from ..utils.log_utils import OUTPUT`.) Always import `OUTPUT` through
the local shim, never from `mcp_coder_utils`.

Replacements (text unchanged unless stated; use `%s` lazy formatting):

| Where | Old | New |
|---|---|---|
| `_env.run` | `print(">", pretty + cwd_hint)` | `logger.log(OUTPUT, "> %s%s", pretty, cwd_hint)` |
| `_env.ensure_system_uv` | `print("--- uv not on PATH; …")` | `logger.log(OUTPUT, …)` |
| `phase_venv` | `print(f"--- wiping {venv}")` | `logger.log(OUTPUT, …)` |
| `phase_overrides` | `print(f"--- skipping GitHub overrides …")` | `logger.log(OUTPUT, …)` |
| `phase_report_versions` | `"\n--- installed versions"` | `"--- installed versions"` (no `\n`) |
| `phase_report_versions` | `"  (skipped in --check mode)"`, `"  (not installed: …)"` | `logger.log(OUTPUT, …)` |
| `phase_post_install_checks` | `"\n--- post-install checks"` | `"--- post-install checks"` (no `\n`) |
| `phase_post_install_checks` | `print(f"\nERROR: {n} of {total} post-install checks failed:")` | `logger.error("%d of %d post-install checks failed:", n, total)` |
| `phase_post_install_checks` | `print(f"  {argv}: {reason}")` | `logger.log(OUTPUT, "  %s: %s", …)` |
| `install()` | `"=== mcp-coder install -> …"`, `"    source: …"` | `logger.log(OUTPUT, …)` |
| `install()` | `"\nOK  mcp-coder install complete: …"` | `"OK  mcp-coder install complete: …"` (no `\n`) |

Leave the `sys.exit(...)` messages (`rmtree_with_retry`, `ensure_system_uv`) unchanged.
Postcondition: `search_files(pattern="print\\(", glob="src/mcp_coder/install/**")` finds nothing.

## HOW (tests)
- Replace `capsys` with `caplog` in both test files. Set the level per test (or via a
  small autouse fixture per class) with
  `caplog.set_level(OUTPUT, logger="mcp_coder.install")` — the root level is WARNING,
  which drops `OUTPUT` records. Import `OUTPUT` from `mcp_coder.utils.log_utils`.
- Read output from `caplog.messages` (list of formatted messages).
- `_run_install_check(caplog, **overrides)` in `test_install_phases.py`: return
  `[m[2:].rstrip() for m in caplog.messages if m.startswith("> ")]`. Update the module
  docstring ("capture stdout" → "read the log records").
- `test_install_post_checks.py::TestPhasePostInstallChecks::test_dry_run_echoes_declared_argv`:
  same `> ` parsing from `caplog.messages`.
- No vacuous negatives: every "not in" / "== []" assertion is paired with a positive
  assertion that proves capture is live, e.g.
  - `test_no_checks_declared_is_silent`: `caplog.messages == []` (the phase returns
    before logging anything — keep, it is a real assertion on records).
  - `TestPhaseVersions::test_present_binaries_are_queried`: also assert
    `"--- installed versions" in caplog.messages`.
  - `TestInstallDriver::test_failure_suppresses_complete_line`: `"  nowhere: not found"`
    present and no message contains `"install complete"`.
- New assertions in `test_one_failure_exits_with_summary`: the header record has
  `levelno == logging.ERROR`, its message is `"1 of 2 post-install checks failed:"` and
  does not start with `"ERROR:"`; per-check line `"  tool-b --version: exit code 2"`
  is an `OUTPUT` record.
- New assertion (any dry-run test): `"--- installed versions"` and
  `"OK  mcp-coder install complete: …"` messages have no leading `\n`.

## ALGORITHM
None — mechanical replacement.

## DATA
No signature changes. Output moves from stdout (`print`) to the logging handlers
(stderr console handler set up by `cli/main.py`).
