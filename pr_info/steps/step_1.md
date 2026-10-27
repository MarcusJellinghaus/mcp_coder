# Step 1 — Write `quality-and-security-checks.md`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`). Create
> `docs/repository-setup/quality-and-security-checks.md` as specified below. Verify every
> fact against the current `ci.yml`, `pyproject.toml`, `tools/check_*.py`,
> `.github/workflows/*.yml` and `.github/dependabot.yml` before writing it. Do not copy from
> `python.md`, `github.md` or `repo.md`. Follow the CLAUDE.md writing style. Docs only: do
> not change any config or code. Run `check_file_size`, check the links by hand, then
> format and commit as one commit.

## WHERE

`docs/repository-setup/quality-and-security-checks.md` (new). All links are relative to
that folder: `../../pyproject.toml`, `../../.github/workflows/ci.yml`, `python.md`, …

## WHAT — document structure

```
# Quality and Security Checks
<one-line intro: which automated checks run on mcp-coder, and why. mcp-coder only.>

## Overview            table: Area | Tool(s) | Why | MCP tool | Links   (13 rows)
## Principles          exactly two bullets
## Tool support        mcp-tools-py, mcp-workspace, gaps
## Lint … ## Badges    13 area sections, 2–4 lines each: why + one key link
```

No rule-by-rule tables, no counts, no todo lists, no source line numbers.

## DATA — content per section

**Principles** (exact meaning):
- Every enabled or rejected choice has a recorded reason, in the config comment or its issue.
- A rule that starts firing later is either fixed or ignored *with a reason*. It is never suppressed silently.

**Tool support:**
- **mcp-tools-py** runs the checks locally: `run_ruff_check`, `run_pylint_check`,
  `run_mypy_check`, `run_pytest_check`, `run_vulture_check`, `run_lint_imports_check`,
  `run_tach_check`, `run_deptry_check`, `run_format_code`, …
  **Do not list `run_bandit_check`.**
- **mcp-workspace** reads CI and PR status (`check_branch_status`, `github_pr_view`), so the
  LLM can review CI results and failure logs after a push. It also provides `check_file_size`.
- Gaps (bash, mcp-coder CLI or CI only): pycycle, the Repo hygiene scripts, CodeQL,
  Scorecard, Dependabot, `mcp-coder verify`.

**Area sections** (facts verified on `main` when this plan was written; re-check them):

| Area | Content | MCP tool |
|---|---|---|
| Lint | ruff rule groups #1164–#1172 (`TRY` rejected, #1172). Selection also has `D` (Google convention), `PLW1510`, `PLE2502`, `I` (#1175). Gotcha: `explicit-preview-rules = true`, so preview rules fire only by exact code; a bare `DOC` prefix enforces nothing. CI job `ruff`. | `run_ruff_check` |
| Formatting | `ruff format` + ruff `I` replaced black and isort (#1175): one tool, no two sorters disagreeing. CI: `ruff-format` (format), `ruff` (import order). Both cover `src`, `tests`, `tools`. | `run_format_code` |
| Types | mypy strict, CI job `mypy`. Plus `upstream-compat-check.yml`: mypy strict + import check of every module against upstream main of mcp-coder-utils, mcp-workspace, mcp-tools-py (`repository_dispatch`, `workflow_dispatch`). | `run_mypy_check` |
| Pylint | Errors and warnings; `C` and `R` off except `R0401`. Runs alongside ruff because ruff does not fully cover pylint. Both stay. No retirement note. CI job `pylint`. | `run_pylint_check` |
| Architecture | import-linter (`.importlinter`), tach (`tach.toml`), pycycle, vulture in the PR-only `architecture` matrix (deptry too, see Dependencies). Pylint `R0401` (cyclic imports) runs on every push. | `run_lint_imports_check`, `run_tach_check`, `run_vulture_check`; pycycle — |
| File size | Small files suit an LLM's limited context window. CI `file-size`: `mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist`. Locally `check_file_size` is equivalent: it applies `.large-files-allowlist`, and `.mcp.json` sets `--file-size-limit 750`. Link `repo.md`. | `check_file_size` |
| Dependencies | deptry (#1176, `[tool.deptry]`, PR-only `deptry` job). Dependabot `pip` + `github-actions` (`.github/dependabot.yml`). | `run_deptry_check`; Dependabot — |
| Coverage | Reported, never a gate (#1178): `coverage` job → diff-cover summary on PRs, gist badge on main. Local digest: `run_pytest_check(coverage=True)`. | `run_pytest_check` |
| Security scanning | ruff `S` (with filters, #1170) and `PLE2502` (replaces bandit `B613`); bandit dropped (#1177). CodeQL default setup (no workflow file). OpenSSF Scorecard (`scorecard.yml`, weekly and on main, SARIF upload). Inline note: the `verify` CodeQL `[OK]` comes from the Scorecard `upload-sarif` step matching the `github/codeql-action/*` prefix; default setup itself is not detected (see the #1163 comments). | `run_ruff_check`; CodeQL/Scorecard — |
| Tests | pytest jobs `unit-tests`, `integration-tests`, `langchain-integration`, split by markers (`pyproject.toml` `[tool.pytest.ini_options]`). `vscodeclaude-template-install` is out. | `run_pytest_check` |
| Repo hygiene | `check-forbidden-folders`: PR-only; blocks `pr_info/`, `.scratch/`, non-empty profiler output. `no-url-deps` (`tools/check_no_url_deps.py`): no direct URL deps in `[project]` dependencies/extras; PyPI rejects them. `forbidden-calls` (`tools/check_forbidden_calls.py`): regex scan of `src/`; describe the rules the script has **at implementation time** (on writing this plan: literal `["git", …]` argv, plus direct `mcp_workspace.git_operations` / `github_operations` imports outside their shims; #1350 may change this). | — |
| Repo settings | `mcp-coder verify` GITHUB SECURITY section (#1179, #1180; link `github.md#repo-security-configuration-checks`), branch rulesets (#1294). Dependabot is covered only in Dependencies and not repeated here; this section links to the `verify` Dependabot rows in addition to the GITHUB SECURITY section. **Job-name rule (this doc is its home):** required status checks must match CI job names; matrix entries report under their `name`, and a renamed or removed job blocks every PR. | — |
| Badges | Transparency: anyone sees the check state at a glance (#1291). Setup stays in `github.md#readme-badges`. | — |

## ALGORITHM

```
for each area: re-read its source file(s) on main; correct the DATA row if it changed
write intro, Overview table (13 rows, Links column = full link list)
write Principles, Tool support
write 13 area sections (2–4 lines, why + one key link)
check_file_size; open every relative link/anchor and confirm it exists
run_format_code; commit "docs: add quality and security checks overview (#1181)"
```

## Verification

- `mcp__mcp-workspace__check_file_size` passes.
- Every relative link points to an existing file; every `#anchor` matches a heading.
- No Python changed, so pylint/mypy/pytest are not required for this step.
