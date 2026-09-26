# Implementation review log 2 — issue #1151

Continuation of `implementation_review_log_1.md` (3 rounds, ended on a dismissed
low-severity finding + rebase note). Branch status at start of this run: CI=PASSED,
Rebase=UP_TO_DATE, Tasks=COMPLETE, PR=NOT_FOUND.


## Round 1 — 2026-09-26
**Findings**:
- `src/mcp_coder/install/__init__.py:23-27` — low — `__all__` still exports `MCP_CODER_REPO`, `REPORT_BINARIES`, `REPORT_PACKAGES` alongside `InstallConfig`/`install`, but nothing imports them from the package (tests import from `._env` directly). Contradicts Decision 12's stated public shape.
- `tools/reinstall_local.bat:12` — low — repo-venv filter does a literal string compare (`%MCP_CODER_VENV_PATH%` vs `%REPO_BIN%`), so a trailing backslash or 8.3 short-path form defeats it.
- `tools/reinstall_local.sh:23` — low — `for p in $(type -a -P mcp-coder ...)` word-splits on whitespace; a PATH entry containing a space yields a bogus fragment instead of the actionable Decision-22 error.

All three are carry-overs from `implementation_review_log_1.md` (rounds 1–3), previously dropped or explicitly dismissed without a recorded Decisions.md entry overriding them.

**Decisions**:
- `__init__.py:23-27` — **accept**. Bounded, mechanical: trim `__all__`/re-exports to match Decision 12's `InstallConfig` + `install` shape; keep `_env` imports for `_phases`' own use, not re-exported.
- `reinstall_local.bat:12` — **skip**. Fixing this correctly (trailing-slash normalization is a partial fix; true 8.3-short-path robustness is impractical in batch) is disproportionate effort for an edge case that only bites on an already-malformed `MCP_CODER_VENV_PATH`. Matches "only matters when someone makes a future mistake → speculative" (`software_engineering_principles.md`).
- `reinstall_local.sh:23` — **accept**. Small, mechanical fix (switch to a `while IFS= read -r p; do … done <<< "$(type -a -P mcp-coder 2>/dev/null)"` loop) that removes a real word-splitting bug without touching the surrounding logic.

**Changes**: applied — trimmed `mcp_coder.install.__all__` to `InstallConfig`/`install` (Decision 12); fixed `reinstall_local.sh`'s driver-resolution loop to read `type -a -P mcp-coder` output line-by-line instead of word-splitting. pylint, pytest (full fast pass + targeted install/cli suites), mypy, ruff all pass.
**Status**: committed
