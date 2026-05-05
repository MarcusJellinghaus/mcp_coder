# Implementation Review Log — Run 1

**Branch**: `ci-uv-sync`
**PR**: #955 — ci: switch to uv sync, drop redundant URL override workaround
**Date started**: 2026-05-05
**Scope**: CI/config-only diff (`.github/workflows/ci.yml`, `pyproject.toml`). No `pr_info/steps/*` exist for this branch; PR #955 body is the requirements source.

## Goals (from PR #955)

1. Replace `uv pip install --system "${SPECS[@]}" ".[…]"` with `uv sync` in CI; rely on `[tool.uv.sources]` for git-pinned siblings.
2. Drop `[tool.uv].override-dependencies` workaround (no longer needed with current uv).
3. Drop `mcp-config-tool` from `[tool.mcp-coder.install-from-github]` (transitive via mcp-workspace, not directly imported).

## Round 1 — 2026-05-05

**Findings**:
1. **Critical** — `.github/workflows/langchain-integration.yml:50-53` still uses the old `mapfile + uv pip install --system "${SPECS[@]}" ".[dev,langchain]"` pattern. Inconsistent with the PR's stated intent to switch CI to `uv sync`.
2. **Accept** — `tools/read_github_deps.py` is no longer used by the migrated CI matrices, but remains used by `tools/reinstall_local.{bat,sh}` and (before this round) `langchain-integration.yml`.
3. **Accept** — Matrix `extras` block in `ci.yml` correct; old `install: ".[typecheck]"` references all removed.
4. **Accept** — Both CI matrices run on `ubuntu-latest`, so `$GITHUB_WORKSPACE/.venv/bin` path is correct.
5. **Skip** — `[tool.uv.sources]` reordering is cosmetic (unordered mapping).
6. **Skip** — Pre-existing trailing whitespace on a few lines; not introduced here.
7. **Skip** — `mcp-config-tool` removal confirmed not imported anywhere in `mcp_coder` source.
8. **Skip** — `lint-imports` (23/23 contracts kept) and `vulture` clean — no regressions.

**Decisions**:
- #1: **Accept, fix this round.** Same pattern as `ci.yml` migration; bounded effort; staying on the old install path in one workflow undermines the PR's stated goal.
- #2: **Skip.** Script remains legitimately used by local-dev reinstall scripts after #1; not orphaned. No deletion needed.
- #3, #4, #7, #8: **No action** — already correct.
- #5, #6: **Skip** — cosmetic / pre-existing per knowledge_base guidance.

**Changes**:
- Migrated `.github/workflows/langchain-integration.yml` install step from `mapfile + uv pip install --system "${SPECS[@]}" ".[dev,langchain]"` to `uv sync --extra dev --extra langchain` + an `Activate venv` step matching `ci.yml`. No other parts of the file touched.
- Verified `lint-imports` (23/23 contracts kept) and `vulture` (no output) still clean.

**Status**: Committed (`dc5603f2` — "ci: migrate langchain-integration workflow to uv sync").

## Round 2 — 2026-05-05

**Findings**:
1. **Skip** — `.github/workflows/upstream-mypy-check.yml` still uses the old `uv pip install --system` pattern. Pre-existing and intentional — file's own comment requires upstream packages installed from git **before** `.[typecheck]` so uv's resolver does not replace them. Out of scope for this PR.
2. **Skip** — `tools/read_github_deps.py` still actively used by `tools/reinstall_local.bat` and `tools/reinstall_local.sh` for local reinstall flow. Not orphaned. Migrating local reinstall scripts is a separate refactor.
3. **No action** — `pyproject.toml` `[tool.uv.sources]` correctly lists 3 of 4 siblings; `mcp-config-tool` is intentionally absent (transitive via `mcp-workspace`, not in `[project].dependencies`).
4. **No action** — `[tool.uv]` block contains only `constraint-dependencies`; no stale `override-dependencies` comment.
5. **No action** — `[tool.mcp-coder.install-from-github].packages` correctly drops `mcp-config-tool`, retains the three direct siblings.
6. **No action** — `Activate venv` step placement and content consistent across `ci.yml` (test + architecture matrices) and `langchain-integration.yml`.
7. **No action** — `extras: "typecheck"` matrix entry correctly paired with conditional install branch.
8. **Skip** — Incidental trailing-whitespace cleanup; acceptable boy-scout edits.

**Decisions**: All Skip / No action. Zero code changes this round.

**Tool checks (supervisor-run, per skill step 8)**:
- `run_vulture_check`: clean (no output)
- `run_lint_imports_check`: 23/23 contracts kept, 0 broken

**Status**: No changes — loop terminates.

## Final Status

- **Rounds run**: 2
- **Code commits produced this review**: 1 (`dc5603f2` — `ci: migrate langchain-integration workflow to uv sync`)
- **Vulture**: clean
- **Import-linter (lint-imports)**: 23/23 contracts kept
- **PR goal status** (vs PR #955 body):
  1. Switch CI to `uv sync` + `Activate venv` — **achieved** (`ci.yml` test + architecture matrices, `langchain-integration.yml`)
  2. Drop `[tool.uv].override-dependencies` — **achieved**
  3. Drop `mcp-config-tool` from `install-from-github` — **achieved**
- **Out-of-scope items noted**: `upstream-mypy-check.yml` retains old pattern by design (intentional ordering requirement, in-file comment). `tools/read_github_deps.py` retained for `reinstall_local.{bat,sh}`.
- **No outstanding findings.**
