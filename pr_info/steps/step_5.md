# Step 5 — Remove the four unused transitive dependencies + regenerate dependency docs

**Goal:** Drop the dependencies `mcp_coder` declares but never imports directly
(`GitPython`, `PyGithub`, `structlog`, `python-json-logger`), prune the two
isolation contracts that no longer guard a declared dep, and regenerate /
hand-fix the dependency documentation so it reflects the final package set. One
commit.

**Runs last** so the regenerated graph and the contract-count prose reflect every
package removed across Steps 2 and 4 as well.

This step touches no `src/` code (these packages are not imported directly), so
there is no new test to write — the gate is that the **existing** suite plus
lint-imports and vulture still pass with the deps gone.

## WHERE

- `pyproject.toml`
- `.importlinter`
- `docs/architecture/dependencies/readme.md`
- `docs/architecture/dependencies/*` (generated graph artifacts)

## WHAT

- `pyproject.toml` → `[project] dependencies`: remove
  - `"GitPython>=3.1.0",`
  - `"PyGithub>=1.59.0",`
  - `"structlog>=23.2.0",`
  - `"python-json-logger>=3.3.0",`
  Keep `black`, `isort`, `requests`, `python-jenkins`, and everything else.
- `.importlinter`: remove the contract blocks
  `[importlinter:contract:structlog_isolation]` and
  `[importlinter:contract:jsonlogger_isolation]`. **Keep**
  `git_library_isolation` and `github_library_isolation` (GitPython / PyGithub
  remain forbidden-from-direct-import guards even though the direct dependency is
  dropped — they are provided via `mcp-workspace`).
- `docs/architecture/dependencies/readme.md` line ~77: this prose lists the
  **import-linter third-party isolation contracts**, not pydeps nodes. After this
  PR the removed contracts are `claude_code_sdk` (Step 4), `pyperclip` (Step 2),
  `structlog`, `pythonjsonlogger` (this step). Update to:
  ```
  **Third-party (7)**: github, git, jenkins, mcp_tools_py, requests, black, isort
  ```
- Regenerate the dependency graph artifacts by running the project's tooling
  (from repo root, in the project venv):
  - `tools/pydeps_graph.sh` (or `.bat`) → updates `pydeps_graph.dot` / `.svg`
  - `python tools/tach_docs.py` → updates `dependency_graph.html`
  Commit whatever the tools produce. If the tooling cannot run in this
  environment (missing GraphViz / pydeps), note that in the commit body and leave
  the generated binaries unchanged — the **required** manual edit is the
  `readme.md` contract line above; the graph is best-effort.

## HOW (integration points)

- These four packages are reached only transitively: GitPython/PyGithub through
  `mcp_workspace_git` / `mcp_workspace_github` (the shims, backed by
  `mcp-workspace`); structlog/python-json-logger through `utils/log_utils`
  (backed by `mcp-coder-utils`). No `mcp_coder` module imports them, so removal is
  source-invisible — `run_lint_imports_check` (which uses
  `include_external_packages = True`) confirms nothing in `mcp_coder` imports
  `git` / `github` / `structlog` / `pythonjsonlogger` directly.
- **Risk accepted (per issue):** if an upstream shim ever drops one of these,
  `mcp_coder` breaks silently. This is the documented trade-off.

## ALGORITHM

None.

## DATA

No runtime data changes; dependency manifest and contract docs only.

## VERIFY

Reinstall the project so the dropped deps actually leave the venv (e.g.
`tools/reinstall_local.*`), then run formatter, pylint, mypy, pytest (`-n auto`
unit subset), `run_lint_imports_check`, and `run_vulture_check` — all green.
Spot-check that logging (`utils/log_utils`) and git/github shim operations still
import and work via their upstream providers. `git grep` for `GitPython`,
`structlog`, `python-json-logger`, `PyGithub` shows only the kept isolation
contracts / shim references, no direct deps.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement Step 5
> only: remove `GitPython`, `PyGithub`, `structlog`, and `python-json-logger` from
> `pyproject.toml` dependencies; remove the `structlog_isolation` and
> `jsonlogger_isolation` contracts from `.importlinter` (keep the GitPython /
> PyGithub isolation contracts); update the third-party contract count/list in
> `docs/architecture/dependencies/readme.md` to `(7): github, git, jenkins,
> mcp_tools_py, requests, black, isort`; and regenerate the dependency graph via
> `tools/pydeps_graph` and `tools/tach_docs.py` (best-effort — note in the commit
> if the tooling can't run). Use MCP workspace tools for edits. Run isort+black
> then `run_pylint_check`, `run_mypy_check`, `run_pytest_check` (unit subset
> `-n auto`), `run_lint_imports_check`, `run_vulture_check`. Fix until all pass,
> then one commit.
