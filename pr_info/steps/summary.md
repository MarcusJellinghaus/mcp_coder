# Issue #922 — Cross-repo CI listener + `[typecheck]` extra

## Goal

This repo (`mcp-coder`) is the **leaf** of a 4-package dependency family. Today, mypy is only available in CI because a transitive dep (likely `textual-dev` in the `[tui]` extra) happens to pull it. If that transitive ever drops mypy, CI breaks silently.

Fix this by:

1. Promoting **mypy** to a first-class declared dep via a new `[typecheck]` extra.
2. Adding a **listener-only** workflow that re-runs `mypy --strict` whenever any of the three upstream repos updates `main` (via `repository_dispatch`).
3. Switching the `mypy` matrix entry in `ci.yml` to install the lean `[typecheck]` extra so the new extra is **load-bearing in regular CI** (not just the new workflow).

This repo only **listens** — no `notify-downstream.yml` is needed (no downstream consumers).

## Architectural / design changes

This is a **CI / packaging** change, not an application code change. No Python source modules are touched.

| Area | Change |
|------|--------|
| Packaging (`pyproject.toml`) | New `[typecheck]` extra: `mypy>=1.13.0` + `mcp-coder[types]`. Reuses the existing `[types]` group so stubs aren't duplicated. |
| CI matrix (`ci.yml`) | `mypy` matrix entry switches from the shared `.[dev,langchain]` install to a per-entry `.[typecheck]` install via a new optional `install` field on the matrix and a `\|\|` fallback in the install step. The other 7 matrix entries (`black`, `isort`, `pylint`, `ruff-docstrings`, `unit-tests`, `integration-tests`, `file-size`) and the `architecture` job are **unchanged**. |
| New workflow (`upstream-mypy-check.yml`) | Triggers on `repository_dispatch` (type `upstream-main-updated`) and `workflow_dispatch`. Installs the three upstream packages from git **first** (with `--no-deps` for `mcp-tools-py` to avoid pulling its dev deps), then `.[typecheck]`. Runs `mypy --strict src tests`. Job-name uses fallback chain `client_payload.upstream \|\| inputs.upstream \|\| github.event_name` so it's never empty. |

### Constraints to preserve

- **Install order** in the new workflow: upstream-from-git **before** `.[typecheck]`. The base `pyproject.toml` has no version pins on those three packages, so `uv`'s resolver leaves the git-installed versions in place. Reordering would silently replace upstream-`main` with PyPI. A YAML comment guards this.
- **`mypy>=1.13.0`** matches the unified target across the 4-repo family.
- **`[typecheck]` is intentionally minimal** — the upstream-from-git install is a CI-only concern handled in the workflow, not in the extra. Local `pip install .[typecheck]` uses whatever upstream version the lockfile resolves to. Asymmetry is intentional.
- **`mypy --strict src tests` must still pass** with only `[typecheck]` installed (plus the three upstream-from-git packages). Existing `[[tool.mypy.overrides]]` already use `ignore_missing_imports` / `follow_imports = "skip"` for langchain/mlflow/etc., so this should hold — but it's the real risk to verify.

## Files created / modified

| File | Change |
|------|--------|
| `pyproject.toml` | **MODIFY** — add `typecheck = ["mypy>=1.13.0", "mcp-coder[types]"]` under `[project.optional-dependencies]`. |
| `tests/test_pyproject_config.py` | **MODIFY** — add a test asserting the `typecheck` extra exists with both required entries. |
| `.github/workflows/upstream-mypy-check.yml` | **CREATE** — listener workflow per issue spec, with install-order comment. |
| `.github/workflows/ci.yml` | **MODIFY** — add `install: ".[typecheck]"` to the `mypy` matrix entry only; switch the `Install dependencies` step to `uv pip install --system "${{ matrix.check.install \|\| '.[dev,langchain]' }}"`. Other 7 entries and the `architecture` job untouched. |

No source modules under `src/`, no folders, no scripts.

## Acceptance criteria mapping

- ✅ Step 1 → `[typecheck]` extra exists with `mypy>=1.13.0` and `mcp-coder[types]`
- ✅ Step 2 → `upstream-mypy-check.yml` exists, parses, contains install-order comment
- ✅ Step 3 → `ci.yml` mypy entry installs `.[typecheck]`; other matrix entries unchanged
- 🟡 Manual triggers (acceptance items 4 & 5) — performed by user in GitHub UI after merge
- 🟡 Cross-repo `repository_dispatch` (acceptance item 6) — depends on companion upstream issues landing first

## Implementation order

1. **Step 1** — `pyproject.toml`: add `[typecheck]` extra (foundation; Step 3 references it)
2. **Step 2** — Create `upstream-mypy-check.yml` (independent of Step 3)
3. **Step 3** — Modify `ci.yml` mypy matrix entry to use `.[typecheck]`

Each step is one commit. Steps 2 and 3 could swap order but Step 1 must come first.

## Notes

- The latent mypy unreachable warning at `src/mcp_coder/utils/tui_preparation.py:121` was fixed pre-implementation in commit `ebd92e0` (platform-guard restructure). All steps verify with green mypy.
