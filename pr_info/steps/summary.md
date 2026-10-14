# Summary: Enable ruff `SIM` with tests carve-out for `SIM117` (#1168)

## Goal

Enable the ruff `SIM` (flake8-simplify) rule set project-wide, with `SIM117`
(multiple-with-statements) carved out for `tests/**/*.py` only — because every
`SIM117` hit there is the standard stacked `with mock.patch(...)` idiom, and
collapsing it produces formatter-wrapped lines that are harder to read and
block per-mock comments. `SIM117` in `src/` is already 0 and must stay 0.

All other `SIM` findings get fixed for real, with two named exceptions that
get a `# noqa: <rule>` instead, because the fix would discard information
(an explanatory comment, or line length/branch symmetry) that has nowhere
else to go.

## Architectural / design changes

This is a lint-policy change, not a runtime architecture change:

- `pyproject.toml`: add `"SIM"` to `[tool.ruff.lint] select`; extend the
  existing `"tests/**/*.py"` per-file-ignore (currently `["D", "DOC"]`) to
  also ignore `SIM117`. `SIM905` is a preview rule (per #1164); with
  `explicit-preview-rules = true` a bare `"SIM"` prefix would silently
  exclude it, so `"SIM905"` is also added as an exact code — the same
  pattern #1164 used for `DOC` — rather than leaving it as an
  undocumented enforcement gap.
- No new modules, abstractions, or behavior. All code changes are local,
  behavior-preserving rewrites of existing control flow at ~31 call sites:
  nested-`if` merges (`SIM102`), `try/except/pass` → `contextlib.suppress`
  (`SIM105`), `if/else` assignment → ternary (`SIM108`), identical `elif`
  bodies merged with `or` (`SIM114`), yoda-condition reversal (`SIM300`),
  manual index → `enumerate`-equivalent cleanup (`SIM113`), `str.split()` on
  a literal → list literal (`SIM905`).
- Two call sites keep their current shape and get a `# noqa: <rule>` with a
  one-line reason instead of a rewrite. This is two specific, individually
  justified exceptions — not a blanket carve-out for `SIM102`/`SIM105` in
  tests.
- No new tests. This issue changes no behavior, so there's nothing new to
  assert. The existing test suite is the regression safety net and must
  stay green through both steps.

## Folders / files touched

Config:
- `pyproject.toml`

Rewritten (no behavior change):
- `src/mcp_coder/checks/file_sizes.py`
- `src/mcp_coder/cli/commands/verify_exit_code.py`
- `src/mcp_coder/icoder/ui/app.py`
- `src/mcp_coder/llm/providers/claude/claude_mcp_guard.py`
- `src/mcp_coder/utils/user_config.py`
- `src/mcp_coder/workflow_utils/commit_operations.py`
- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `src/mcp_coder/icoder/core/event_log.py`
- `src/mcp_coder/install/_env.py`
- `src/mcp_coder/llm/providers/langchain/_errors_404.py`
- `src/mcp_coder/utils/tui_preparation.py`
- `src/mcp_coder/workflow_utils/failure_handling.py`
- `src/mcp_coder/llm/providers/copilot/copilot_cli.py`
- `src/mcp_coder/llm/storage/session_storage.py`
- `src/mcp_coder/utils/folder_deletion.py`
- `src/mcp_coder/workflows/create_plan/prerequisites.py`
- `src/mcp_coder/workflows/utils.py`
- `tests/conftest.py`
- `tests/llm/providers/langchain/test_langchain_integration.py`
- `tests/icoder/test_app_pilot.py`
- `tests/integration/test_mlflow_integration.py`
- `tests/llm/test_types.py`
- `tests/utils/test_git_encoding_stress.py`
- `tests/workflows/vscodeclaude/test_status_display.py`

## Steps

1. **step_1.md** — Resolve every `SIM102/105/108/113/114/300/905` finding in
   `src/` and `tests/`, plus the two `# noqa` exceptions. `SIM` is not yet in
   the project's ruff config at this point, so this step is purely
   preparatory: it makes Step 2's config flip a no-op diff.
2. **step_2.md** — Add `"SIM"` to `[tool.ruff.lint] select` and `"SIM117"`
   to the `tests/**/*.py` per-file-ignore in `pyproject.toml`. Verify
   `ruff check` is clean project-wide and `SIM117` in `src/` is 0.

## Measured counts (re-verified 2026-10-14)

`ruff check --select SIM` over `src/` + `tests/`: **153 findings**, matching
the issue exactly — 120 `SIM117` (tests-only), 13 `SIM102` (11 src / 2
tests), 10 `SIM105` (5 src / 5 tests), 5 `SIM108` (src), 2 `SIM300` (tests),
1 `SIM114` (src), 1 `SIM113` (tests), 1 `SIM905` (tests). Exact locations are
listed in `step_1.md`. Counts drift — re-verify immediately before executing
each step; a mismatch is the blocked condition described in that step.
