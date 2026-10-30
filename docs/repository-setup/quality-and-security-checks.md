# Quality and Security Checks

Which automated checks run on mcp-coder itself, and why. It doubles as a reference setup for
your own Python repository: the MCP tools in the table come from mcp-tools-py and work on any
repo, while the config files, CI jobs and issue numbers are mcp-coder's. Details stay in the
linked config files, docs and issues.

## Overview

| Area | Tool(s) | Why | MCP tool | Links |
|---|---|---|---|---|
| [Lint](#lint) | ruff | Catch bugs, style and docstring gaps in one fast pass | `run_ruff_check` | [`pyproject.toml`](../../pyproject.toml), [`ci.yml`](../../.github/workflows/ci.yml), #1164–#1172, #1175 |
| [Formatting](#formatting) | ruff format, ruff `I` | One tool for layout and import order | `run_format_code` | [`pyproject.toml`](../../pyproject.toml), [`ci.yml`](../../.github/workflows/ci.yml), #1175 |
| [Types](#types) | mypy strict | Catch type errors, including breaks from upstream packages | `run_mypy_check` | [`pyproject.toml`](../../pyproject.toml), [`ci.yml`](../../.github/workflows/ci.yml), [`upstream-compat-check.yml`](../../.github/workflows/upstream-compat-check.yml) |
| [Pylint](#pylint) | pylint | Errors and warnings ruff does not cover | `run_pylint_check` | [`pyproject.toml`](../../pyproject.toml), [`ci.yml`](../../.github/workflows/ci.yml) |
| [Architecture](#architecture) | import-linter, tach, vulture, pylint `R0401` | Keep module boundaries, no cycles, no dead code | `run_lint_imports_check`, `run_tach_check`, `run_vulture_check` | [`.importlinter`](../../.importlinter), [`tach.toml`](../../tach.toml), [`ci.yml`](../../.github/workflows/ci.yml), [`python.md`](python.md#architecture-enforcement), [`enforcement.md`](../architecture/enforcement.md) |
| [File size](#file-size) | `mcp-coder check file-size` | Small files fit an LLM's context window | `check_file_size` | [`.large-files-allowlist`](../../.large-files-allowlist), [`ci.yml`](../../.github/workflows/ci.yml), [`repo.md`](repo.md#file-size-management), [`enforcement.md`](../architecture/enforcement.md) |
| [Dependencies](#dependencies) | deptry, Dependabot | Declared dependencies match imports; stay current | `run_deptry_check`; Dependabot — | [`pyproject.toml`](../../pyproject.toml), [`dependabot.yml`](../../.github/dependabot.yml), [`python.md`](python.md#dependency-declaration-hygiene), [`enforcement.md`](../architecture/enforcement.md), #1176 |
| [Coverage](#coverage) | pytest-cov, diff-cover | Show what tests reach, without gating | `run_pytest_check` | [`ci.yml`](../../.github/workflows/ci.yml), [`github.md`](github.md#coverage-badge), #1178 |
| [Security scanning](#security-scanning) | ruff `S`, `PLE2502`, CodeQL, OpenSSF Scorecard | Find insecure code and supply-chain risks | `run_ruff_check`; CodeQL/Scorecard — | [`pyproject.toml`](../../pyproject.toml), [`scorecard.yml`](../../.github/workflows/scorecard.yml), #1170, #1177 |
| [Tests](#tests) | pytest | Behaviour stays correct | `run_pytest_check` | [`pyproject.toml`](../../pyproject.toml), [`ci.yml`](../../.github/workflows/ci.yml) |
| [Repo hygiene](#repo-hygiene) | CI job, `tools/check_*.py` | Keep scratch files, URL deps and forbidden calls out | — | [`ci.yml`](../../.github/workflows/ci.yml), [`check_no_url_deps.py`](../../tools/check_no_url_deps.py), [`check_forbidden_calls.py`](../../tools/check_forbidden_calls.py) |
| [Repo settings](#repo-settings) | `mcp-coder verify`, branch rulesets | GitHub security features and required checks are on | — | [`github.md`](github.md#repo-security-configuration-checks), #1179, #1180, #1294 |
| [Badges](#badges) | README badges | Check state visible at a glance | — | [`github.md`](github.md#readme-badges), #1291 |

## Principles

- Every enabled or rejected choice has a recorded reason, in the config comment or its issue.
- A rule that starts firing later is either fixed or ignored with a reason. It is never
  suppressed silently.

## Tool support

- **mcp-tools-py** runs the checks locally: `run_ruff_check`, `run_ruff_fix`,
  `run_pylint_check`, `run_mypy_check`, `run_pytest_check`, `run_vulture_check`,
  `run_lint_imports_check`, `run_tach_check`, `run_deptry_check`, `run_format_code`.
- **mcp-workspace** reads CI and PR status (`check_branch_status`, `github_pr_view`), so the
  LLM can review CI results and failure logs after a push. It also provides `check_file_size`.
- **Gaps** (bash, mcp-coder CLI or CI only): the [Repo hygiene](#repo-hygiene)
  scripts, CodeQL, Scorecard, Dependabot, `mcp-coder verify`.

## Lint

ruff, with rule groups chosen in #1164–#1172 (`TRY` rejected, #1172), plus `D` (Google
convention), `PLW1510`, `PLE2502` and `I` (#1175). Gotcha: `explicit-preview-rules = true`, so
preview rules fire only when selected by exact code; a bare `DOC` prefix enforces nothing.
CI job `ruff`. See [`pyproject.toml`](../../pyproject.toml) `[tool.ruff.lint]`.

## Formatting

`ruff format` plus ruff `I` replaced black and isort (#1175): one tool, no two sorters
disagreeing. CI jobs `ruff-format` (format) and `ruff` (import order), both over `src`,
`tests` and `tools`. See [`ci.yml`](../../.github/workflows/ci.yml).

## Types

mypy strict, CI job `mypy`. [`upstream-compat-check.yml`](../../.github/workflows/upstream-compat-check.yml)
runs mypy strict and an import check of every module against upstream main of
mcp-coder-utils, mcp-workspace and mcp-tools-py, on `repository_dispatch` or
`workflow_dispatch`, so interface breaks show before a release.

## Pylint

Errors and warnings; `C` and `R` are off except `R0401` (cyclic imports). It runs alongside
ruff because ruff does not fully cover pylint. CI job `pylint`. See
[`pyproject.toml`](../../pyproject.toml) `[tool.pylint.messages_control]`.

## Architecture

import-linter ([`.importlinter`](../../.importlinter)), tach ([`tach.toml`](../../tach.toml)),
and vulture run in the PR-only `architecture` matrix (deptry too, see
[Dependencies](#dependencies)). Pylint `R0401` catches cyclic imports on every push. See
[`python.md`](python.md#architecture-enforcement). Why: [`enforcement.md`](../architecture/enforcement.md).

## File size

Small files suit an LLM's limited context window. CI job `file-size` runs
`mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist`. Locally
`check_file_size` is equivalent: it applies `.large-files-allowlist`, and `.mcp.json` sets
`--file-size-limit 750`. See [`repo.md`](repo.md#file-size-management). Why:
[`enforcement.md`](../architecture/enforcement.md).

## Dependencies

deptry (#1176, `[tool.deptry]`) checks that declared dependencies match the imports in `src`;
PR-only CI job `deptry`. Dependabot updates `pip` and `github-actions` dependencies. See
[`dependabot.yml`](../../.github/dependabot.yml). Why: [`enforcement.md`](../architecture/enforcement.md).

## Coverage

Reported, never a gate (#1178). The `coverage` job writes a diff-cover summary on PRs and
updates a gist badge on main. Local digest: `run_pytest_check(coverage=True)`. See
[`ci.yml`](../../.github/workflows/ci.yml).

## Security scanning

ruff `S` (with filters, #1170) and `PLE2502` (replaces bandit `B613`); bandit was dropped
(#1177). CodeQL runs as default setup (no workflow file). OpenSSF Scorecard
([`scorecard.yml`](../../.github/workflows/scorecard.yml)) runs weekly and on main and uploads
SARIF to code scanning.

Note: `mcp-coder verify` reports CodeQL `[OK]` only because Scorecard's `upload-sarif` step
matches the `github/codeql-action/*` prefix. Default setup itself is not detected (see the
#1163 comments).

## Tests

pytest jobs `unit-tests`, `integration-tests` and `langchain-integration`, split by markers.
See [`pyproject.toml`](../../pyproject.toml) `[tool.pytest.ini_options]`.

## Repo hygiene

- `check-forbidden-folders` (PR-only): blocks `pr_info/`, `.scratch/` and non-empty profiler
  output.
- `no-url-deps` ([`check_no_url_deps.py`](../../tools/check_no_url_deps.py)): no direct URL
  dependencies in `[project]` dependencies or extras; PyPI rejects them.
- `forbidden-calls` ([`check_forbidden_calls.py`](../../tools/check_forbidden_calls.py)):
  text scan of `src/` for literal `["git", …]` argv lists, and for direct
  `mcp_workspace.git_operations` / `github_operations` imports outside their shims. Why:
  [`enforcement.md`](../architecture/enforcement.md#shim-boundary).

## Repo settings

`mcp-coder verify` reports the GITHUB SECURITY section (#1179, #1180), including the
Dependabot rows; see [`github.md`](github.md#repo-security-configuration-checks). Branch
rulesets (#1294) set the required status checks.

**Job-name rule:** required status checks must match CI job names. Matrix entries report
under their `name`. A renamed or removed job blocks every PR until the ruleset is updated.

## Badges

Transparency: anyone sees the check state at a glance (#1291). Setup stays in
[`github.md`](github.md#readme-badges).
