# Summary — #1173 Route mcp_coder formatting through mcp-tools-py resolution; unify the `format_code` switch

## Goal

- mcp_coder stops hardcoding isort + black. The formatter is chosen by mcp-tools-py's
  `resolve_steps` (`[tool.mcp-tools-py] formatter`, else `[tool.ruff.format]` vs `[tool.black]`),
  the same resolution agent sessions get from the MCP `run_format_code` tool.
- One switch `[tool.mcp-coder] format_code` (default `true`) governs every mcp_coder entry point
  that formats. `[tool.mcp-coder.implement] format_code` is no longer read.
- Formatter config errors are fatal and surface before any LLM call; formatter step failures keep
  today's per-site handling.
- `mcp-coder verify` shows the switch, the resolved formatter steps, a leftover-key `[ERR]`, and exits
  non-zero on any `[ERR]`.

## Architectural / design changes

| Before | After |
|---|---|
| Wrapper `mcp_tools_py.run_format_code` imports `run_isort` / `run_black` and loops over them | Wrapper is a logic-free delegate to `mcp_tools_py.formatter.runner.run_format_code(..., steps=None)`; re-exports `resolve_steps` (import-linter `mcp_checker_isolation`) |
| `format_code` gate in two implement call sites; rebase, review and ci-fix format unconditionally | Gate lives only inside `workflow_steps.commit.run_formatters`; rebase routed through it; implement's checks removed |
| Switch under `[tool.mcp-coder.implement]`, default `False` | `[tool.mcp-coder] format_code`, default `True`, read by `get_format_code()` → `FormatCodeSetting(enabled, explicit)`; non-bool → `ValueError` |
| `run_formatters` swallows every exception | New `FormatterConfigError(ValueError)` propagates; everything else still → `False` |
| No up-front formatter check | `check_formatter_config(project_dir, warn_legacy_key=False) -> str \| None` called as a pre-flight by each formatting entry point (fails via its deliberate fail path) and by `run_formatters` (backstop, raises) |
| verify shows `format_code` from implement config; PROJECT section never affects exit | PROJECT section returns `bool`; rows for `format_code`, Formatter (resolved steps / error), leftover key; `project_ok` feeds `_compute_exit_code` |

### Key design points (KISS)

- **Single source of truth for the formatter:** mcp-tools-py's `resolve_steps`. No mcp_coder-side step list.
- **Single gate:** `run_formatters`. Callers never check `format_code` themselves.
- **Single helper:** `check_formatter_config` returns the error text; entry points map it onto their
  existing fail path; `run_formatters` raises `FormatterConfigError` with it.
- **Rebase pre-flight** is the last check inside the existing `_preflight()` (same log line, exit 2).
- **Legacy key warning** only from entry-point pre-flights (`warn_legacy_key=True`), never from the
  backstop → logged once per run. Old value ignored (no fallback).
- **Tests:** one autouse fixture in `tests/conftest.py` patches
  `mcp_coder.workflow_steps.commit.resolve_steps` (the single lookup site behind every pre-flight and the
  backstop) so project dirs without `pyproject.toml` keep working. Real formatting is unaffected (the
  wrapper uses mcp-tools-py's own `resolve_steps`). Tests of the helper itself re-patch it.
  `tests/cli/commands/conftest.py` gets an autouse patch of `verify._print_project_section` → `True`
  (same pattern as the existing `verify_git` / `verify_github` autouse mocks).

## Files created / modified

### Source
| File | Change |
|---|---|
| `src/mcp_coder/mcp_tools_py.py` | Delegate to mcp-tools-py runner with `steps=None`; re-export `resolve_steps` |
| `src/mcp_coder/utils/pyproject_config.py` | Add `FormatCodeSetting`, `get_format_code`, `has_legacy_format_code_key`; drop `ImplementConfig.format_code` |
| `src/mcp_coder/workflow_steps/commit.py` | Add `FormatterConfigError`, `check_formatter_config`; gate + narrowed except in `run_formatters` |
| `src/mcp_coder/workflow_steps/ci.py` | `check_and_fix_ci` `Raises:` gains `FormatterConfigError` (one line) |
| `src/mcp_coder/workflows/rebase.py` | Formatter check in `_preflight`; fix loop calls `run_formatters` |
| `src/mcp_coder/workflows/review/core.py` | Pre-flight at top of `body()` |
| `src/mcp_coder/workflows/fix_ci/core.py` | Pre-flight at top of `body()` |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Pre-flight in `_run_auto_fixes` |
| `src/mcp_coder/cli/commands/verify_sections.py` | New PROJECT rows; `_print_project_section` returns `bool` |
| `src/mcp_coder/cli/commands/verify.py` | Capture `project_ok`, pass to `_compute_exit_code` |
| `src/mcp_coder/cli/commands/verify_exit_code.py` | `project_ok: bool = True` parameter |
| `src/mcp_coder/workflows/implement/core.py` | Pre-flight at top of `body()`; remove gate and `format_code` kwarg |
| `src/mcp_coder/workflows/implement/task_processing.py` | Remove `format_code` parameter and gate |

### Tests
| File | Change |
|---|---|
| `tests/conftest.py` | Autouse fixture patching `commit.resolve_steps` |
| `tests/cli/commands/conftest.py` | Autouse patch of `verify._print_project_section` |
| `tests/test_mcp_tools_py.py` | Wrapper delegate tests |
| `tests/utils/test_pyproject_config.py` | New accessor tests; drop `format_code` from implement-config tests |
| `tests/test_pyproject_config.py` | Drop `implement["format_code"]` assertion |
| `tests/workflow_steps/test_commit.py` | Gate / error / helper tests; revise generic-exception test |
| `tests/workflows/rebase/test_workflow.py`, `test_guards.py` | Patch `run_formatters`; `_preflight` formatter check |
| `tests/workflows/review/` (new test in an existing or new file) | Pre-flight test |
| `tests/workflows/fix_ci/test_core.py` | Pre-flight test |
| `tests/cli/commands/test_check_branch_status_auto_fixes.py` | Pre-flight test |
| `tests/cli/commands/test_verify_project_section.py` (**new**) | Verify row + exit tests |
| `tests/cli/commands/test_verify.py` | Adjust `_print_project_section` tests (`:650-737`) |
| `tests/cli/commands/test_verify_exit_codes.py` | `project_ok=False` → 1 |
| `tests/workflows/implement/test_core.py`, `test_task_processing.py` | Remove `format_code` plumbing tests; add pre-flight test |

### Config / text / docs
| File | Change |
|---|---|
| `pyproject.toml` | Delete `format_code = true` under `[tool.mcp-coder.implement]` |
| `.claude/CLAUDE.md`, `.claude/skills/commit_push/SKILL.md`, `.claude/skills/implement_direct/SKILL.md` | "black+isort" → the project's configured formatter |
| `docs/repository-setup/python.md`, `docs/configuration/config.md`, `docs/repository-setup/claude-code.md`, `docs/processes-prompts/development-process.md` | See step 9 |

## Steps

1. Wrapper delegates to mcp-tools-py resolution
2. Config accessors + single gate in `run_formatters` (+ root test fixture)
3. Rebase: formatter pre-flight in `_preflight`, fix loop via `run_formatters`
4. Review pre-flight
5. fix-ci pre-flight
6. `check_branch_status --fix` pre-flight
7. verify rows + exit code
8. implement: pre-flight, remove old `format_code` plumbing, remove repo key
9. Text and docs

## Out of scope (do not touch)

`docs/architecture/architecture.md:408`, `docs/repository-setup/github.md:418, :441`,
`docs/repository-setup/python.md:179-180, :200, :211`,
`docs/processes-prompts/development-process.md:723`, `docs/architecture/dependencies/readme.md:77`,
sibling repos and shipped templates.
