# Implementation Review Log — Issue #640

Reviewer: Supervisor agent
Date started: 2026-04-06

## Round 1 — 2026-04-06

**Findings:**
1. *Important* — `get_github_install_config` in `pyproject_config.py` doesn't catch `TOMLDecodeError`/`OSError`, unlike sibling `get_formatter_config`.
2. *Important* — `reinstall_local.bat` `for /f` loop silently swallows `read_github_deps.py` Python errors (zero-output success path).
3. *Important* — `_check_line_length_conflict` in `formatters/__init__.py` applies tool defaults differently from public `check_line_length_conflicts`; risk of maintainer confusion.
4. *Minor* — Self-alias re-export in `config_reader.py` could use `__all__`.
5. *Minor* — Default `pyproject.toml` path resolves via CWD (no behavior change).
6. *Minor* — Launcher version prints have no error handling/comment.
7. *Minor* — `tools/read_github_deps.py` not in vulture/pylint/ruff scan targets.

**Decisions:**
- Accept #1 — bounded fix for real inconsistency.
- Accept #2 — real failure mode that could mask broken bootstraps.
- Accept #3 (comment-only) — Boy Scout fix; clarifies intent without behavior change.
- Skip #4 — `as X` is standard PEP 484 re-export idiom; speculative cleanup.
- Skip #5 — no behavior change.
- Skip #6 — issue #640 explicitly specifies plain calls without error handling.
- Skip #7 — `tools/` is intentionally outside scan targets (bootstrap helpers).

**Changes:**
- `src/mcp_coder/utils/pyproject_config.py` — wrapped `get_github_install_config` parse in `try/except (tomllib.TOMLDecodeError, OSError)`.
- `tools/reinstall_local.bat` — pre-validates `read_github_deps.py` exit code; on failure, re-runs visibly then exits with 1.
- `src/mcp_coder/formatters/__init__.py` — added clarifying docstring contrasting `_check_line_length_conflict` with public `check_line_length_conflicts`.

All five MCP quality checks passed.

**Status:** committed `c073c8c`, pushed.

## Round 2 — 2026-04-06

**Findings:** No new findings. Round 1 fixes verified correct, no new issues introduced, no actionable items missed.

**Decisions:** N/A.

**Changes:** None.

**Status:** No code changes — review loop terminates.

## Final Status

- Rounds run: 2
- Commits produced this review: 1 (`c073c8c`)
- Outstanding issues: none
- All accepted findings implemented and verified
