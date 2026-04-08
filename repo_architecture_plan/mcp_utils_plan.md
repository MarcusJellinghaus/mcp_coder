# mcp-utils Extraction Plan — Module Inventory

Planning doc for introducing a shared `mcp-utils` repo across the 4 existing repos.
Every module in every repo is listed below with a proposed disposition. Nothing is final — this is the working surface for decisions.

> ⚠️ **Validation status.** Phase 0 source-read validation is **complete for phase 2 modules** (`subprocess_runner`, `subprocess_streaming`, `log_utils`) — see "Phase 0 findings" section below. Validation for phase 4 (formatters, pyproject_config split) and phase 5 (git, github) is **deferred to just-in-time** — read the source of those modules immediately before starting each phase.

**Legend:**

- 🟢 **MOVE** — move to `mcp-utils`
- 🔴 **KEEP** — stays in current repo (domain-specific)
- 🟡 **TBD** — needs discussion
- ⚫ **CONSOLIDATE** — duplicate of another repo's module; pick one source of truth
- ✨ **NEW** — new module in `mcp-utils`

---

## 0. Architectural rules

These rules decide where any piece of code lives. Apply them *before* debating individual modules.

1. **MCP-first (DRY).** If functionality can be exposed as an MCP tool, it lives in an MCP server — not in `mcp_coder`. `mcp_coder` orchestrates; servers execute. If something exists in both, the server copy wins and the `mcp_coder` copy is deleted.
2. **One server per domain.** Split MCP servers by functional area. Current: `mcp_tools_py` (Python ecosystem), `mcp_workspace` (local checkout + git, and temporarily: GitHub). Possible future (for illustration): `mcp_github`, `mcp_jenkins`, `mcp_tools_sql`, …
3. **`mcp-utils` = code used by ≥2 MCP servers.** Shared *across servers*, not across repos. `mcp_coder` and `mcp_config` are consumers — their usage does not justify a move into `mcp-utils`. If only one server needs a helper, it lives in that server. If only `mcp_coder` needs it, it stays in `mcp_coder`.
4. **`mcp-utils` is strictly language-agnostic.** Zero knowledge of Python, .NET, Java, SQL, or any other ecosystem. Anything that parses `pyproject.toml`, knows about venvs, understands `.csproj`, etc. belongs to the relevant language server — never in `mcp-utils`. This is what lets future mcp servers consume `mcp-utils` without dragging Python along.

### Server lineup (current + proposed + future)

| Repo | Kind | Purpose | Status |
|---|---|---|---|
| `mcp_coder` | CLI client | Workflows, LLM providers, icoder TUI. Consumer only. | exists |
| `mcp_tools_py` | MCP server | Python ecosystem: linters, formatters, refactoring, pyproject parsing | exists |
| `mcp_workspace` | MCP server | Local checkout: file ops + git (read & write) | exists |
| `mcp_github` | MCP server | GitHub API: issues, PRs, labels, CI, repo metadata | possible future (for illustration) |
| `mcp_tools_sql` | MCP server | SQL linters, schema tools | possible future (for illustration) |
| `mcp-utils` | library | Code shared by ≥2 MCP servers. Language-agnostic. | **proposed** |
| `mcp_config` | CLI client | Manages MCP client config files. Consumer only. | exists, to be reviewed |

### High-level phased roadmap

Big-picture sequencing of the work. Each phase is a group of tasks, not a single PR. Details of what moves where live in §1–§6.

| Phase | Goal | Scope |
|---|---|---|
| **0. Pre-work** | Unblock decisions before any code moves | Resolve naming (`pyproject_config` vs `project_config`, `file_utils` vs `path_utils`); read `mcp_tools_py/utility_tools.py` to classify it; validate this plan against actual source (per top-of-doc banner) |
| **1. Create `mcp-utils` repo** | New empty repo with project scaffolding | Empty GitHub repo; add baseline features per `docs/repository-setup/`; CI + CD pipelines; initial release tag `v0.1.1` (may be empty or contain just `subprocess_runner` + `log_utils`) |
| **2. First functionality move** | Land the first real modules in `mcp-utils` | `subprocess_runner` + `subprocess_streaming` + `log_utils` — the pure leaves. Tests move with them. Release `v0.1.2` |
| **3. Consumer adoption** | Replace local copies across repos | Register `mcp-utils` as a reference project in each consumer; add "Shared libraries" block to each `CLAUDE.md`; swap imports in `mcp_coder`, `mcp_tools_py`, `mcp_workspace`, `mcp_config`; delete local duplicates |
| **4. mcp_coder → mcp_tools_py** | Consolidate Python-specific code | Move `mcp_coder/formatters/` (whole directory) + `pyproject_config.py` → `mcp_tools_py`. Smaller move, validates the cross-repo move pattern before the bigger one |
| **5. mcp_coder → mcp_workspace** | Consolidate workspace/git/github code | Move `mcp_coder/utils/git_operations/` (entire) + `mcp_coder/utils/github_operations/` (entire) → `mcp_workspace` as MCP tools. Biggest move (~30 files). mcp_coder workflows now call git/GitHub via MCP |
| **6. Finalize** | Clean up and document | Delete now-empty `mcp_coder/utils/*` subdirectories; verify no stale imports remain (grep all 4 repos); update `CLAUDE.md` "Shared libraries" blocks with final public API; close tracking issues |
| **7. Oout of scope** | Documented but no action | `mcp_jenkins` split, `mcp_github` split (§6), `mcp-llm` extraction, `icoder` extraction, `mcp_config` review |

**Ordering rationale:**
- Phase 0 must complete first — unresolved names cause churn mid-migration.
- Phases 1–3 establish the `mcp-utils` mechanism end-to-end with the simplest possible modules.
- Phase 4 (smaller) before Phase 5 (larger) — validate the cross-repo move pattern on ~6 files before attempting ~30.
- Phase 6 is cleanup only; no new moves.
- Phase 7 is explicitly deferred.

---

## 1. `mcp-utils` (NEW repo — proposed)

Strict shape under rules #3 and #4: only modules used by ≥2 MCP servers **and** language-agnostic.

| Module | Source | Notes |
|---|---|---|
| `subprocess/runner` | ✨ from mcp_tools_py + mcp_workspace (+ mcp_coder's version for reference) | used by every server to shell out. Pick mcp_coder's as canonical (most featureful) |
| `subprocess/streaming` | ✨ from mcp_coder | pairs with `subprocess/runner` — moves together |
| `logging/log_utils` | ✨ from mcp_tools_py + mcp_workspace (+ mcp_coder's redaction) | every server needs logging |
| `fs/read_file` | ✨ from mcp_tools_py + mcp_config (literal duplicates) | 30-line UTF-8→latin-1 fallback reader; trivial dedupe |
| `fs/path_security` | ✨ from mcp_workspace's `path_utils.py` | `normalize_path()` — path traversal prevention; different responsibility from read_file |

**That's it for the first cut.** Everything else needs a concrete second-server consumer before it earns a spot here.

### Demoted — do **not** move to mcp-utils

| Module | Why demoted | New home |
|---|---|---|
| `pyproject_config` (mcp_coder) | Python-specific (rule #4) — but NOT a duplicate of p_tools's `project_config`; see Phase 0 findings | **Split:** formatter helpers → `mcp_tools_py/formatter/`; `get_github_install_config` stays in mcp_coder |
| `formatters/config_reader.py` | Reads `[tool.black]` / `[tool.isort]` — Python-specific | `mcp_tools_py` |
| `user_config` | Only mcp_coder uses it | stays in `mcp_coder` |
| `data_files` | Only mcp_coder uses it | stays in `mcp_coder` |
| `folder_deletion` | Only mcp_coder uses it (for now) | stays in `mcp_coder`; revisit if a server needs it |
| `timezone_utils` | Only mcp_coder uses it | stays in `mcp_coder` |
| `clipboard` | Only mcp_coder uses it; may even be deletable | stays in `mcp_coder` |
| `crash_logging` | New; only mcp_coder uses it | stays in `mcp_coder`; revisit if servers crash silently |
| `black_runner` / `isort_runner` | Python-specific | canonical lives in `mcp_tools_py/formatter/`; mcp_coder's duplicate gets deleted and the whole `mcp_coder/formatters/` directory moves there |

### On cross-repo dependencies: always use thin shims

**Rule:** every cross-repo dependency goes through a thin wrapper module in the consuming repo — never scattered imports at call sites.

#### MCP servers expose two entry points

Important for understanding what a shim wraps. Every MCP server (`mcp_tools_py`, `mcp_workspace`, future ones) has **two public surfaces**:

1. **MCP tools** — invoked over the MCP protocol by an LLM (Claude Code, etc.). Example: `mcp__tools-py__run_pylint_check`. This is what Claude calls during a session.
2. **Python modules** — importable directly as normal Python: `from mcp_tools_py.code_checker_pylint import run_pylint`. This is what other Python code (like `mcp_coder` workflows) calls in-process, without going through the MCP protocol.

Both surfaces exist side-by-side. The same underlying function is reachable through either. `mcp_coder` typically uses the **Python module surface** (cheap, in-process, no protocol overhead) — the MCP tool surface is there for Claude.

#### What a shim looks like

A single file in the consuming repo (e.g. `mcp_coder/mcp_tools_py.py`) that re-exports or wraps the imports the consumer actually uses. Call sites import from the shim, not from the dependency directly. The shim hides *which* entry point is in play (MCP tool call vs direct Python import) — call sites just see a clean local function.

#### Why shims

1. **Clean architecture** — one chokepoint per dependency, easy to audit/mock/replace.
2. **Entry-point flexibility** — you can switch a given call from MCP round-trip to direct Python import (or vice versa) by editing one file.
3. **Documented surface area** — the shim is the place to explain *how* to use the dependency, which is also what an LLM reads when working in the repo.
4. **Refactor safety** — if the dependency changes, only the shim updates.

#### Shims don't need unit tests

A shim is a pass-through. Testing it just tests the mock. The real tests live in the source repo (the MCP server's own test suite). What the consumer needs is **integration tests** that exercise the shim against the real dependency — those live in the consumer's own test suite and cover end-to-end flow, not the shim in isolation.

#### When not to shim

`mcp-utils` itself. It is the leaf library; shimming it would defeat the purpose. Consumers import `mcp-utils` functions directly.

### LLM awareness of `mcp-utils`

Since `mcp-utils` is not shimmed, the LLM working in a consumer repo needs another way to know it exists and what's in it. Use both of the following, in combination:

1. **CLAUDE.md section in every consumer repo.** Each of `mcp_coder`, `mcp_tools_py`, `mcp_workspace`, `mcp_config` gets a short "Shared libraries" block listing the top-level imports and the rule "do not reimplement — check mcp-utils first." This is always in context at session start.
2. **Register `mcp-utils` as a reference project.** Use the existing reference-project mechanism (`mcp__workspace__get_reference_projects` / `list_reference_directory` / `read_reference_file`). Add `mcp-utils` to each consumer repo's reference-project configuration so the LLM can read its actual source when needed — the same way this plan was developed against `p_tools`, `p_workspace`, `p_config`.

**Why both:** (1) gives always-on awareness (LLM knows the dep exists without doing any lookup); (2) gives live, accurate source access (no staleness, no manual API docs to maintain).

**Template for the CLAUDE.md block:**

```markdown
## Shared libraries

This repo depends on `mcp-utils` for subprocess/logging/fs helpers.
- `from mcp_utils.subprocess import run_command, run_streaming`
- `from mcp_utils.logging import get_logger`
- `from mcp_utils.fs import ...`

**Do not reimplement these locally.** When in doubt, check mcp-utils first.
Full source: reference project `p_mcp_utils` — use `mcp__workspace__read_reference_file`.
```

---

## 2. `mcp_coder` (current repo)

### Top-level

| Module | Disposition | Notes |
|---|---|---|
| `constants.py` | 🔴 KEEP | project-specific |
| `mcp_tools_py.py` | 🔴 KEEP | shim pointing at mcp_tools_py server |
| `mcp_workspace.py` | 🔴 KEEP | shim pointing at mcp_workspace server |
| `prompt_manager.py` | 🔴 KEEP | workflow-specific |
| `__main__.py` | 🔴 KEEP | |

### `checks/`

| Module | Disposition | Notes |
|---|---|---|
| `branch_status.py` | 🔴 KEEP | PR/branch workflow |
| `ci_log_parser.py` | 🔴 KEEP | GitHub Actions log parsing |
| `file_sizes.py` | 🔴 KEEP | repo check |

### `cli/` + `cli/commands/`

| Module | Disposition | Notes |
|---|---|---|
| all of `cli/` | 🔴 KEEP | mcp_coder is a CLI — this is its identity |
| all of `cli/commands/` | 🔴 KEEP | |
| `cli/commands/coordinator/` | 🔴 KEEP | |

### `config/`

| Module | Disposition | Notes |
|---|---|---|
| `labels.json`, `labels_schema.md` | 🔴 KEEP | project labels |
| `mlflow_config.py` | 🔴 KEEP | mlflow setup |

### `formatters/`

Whole directory moves to `mcp_tools_py/formatter/`. mcp_coder becomes a consumer via a shim.

| Module | Disposition | Notes |
|---|---|---|
| `black_formatter.py` | 🟢 MOVE → `mcp_tools_py/formatter/` | merge with existing `black_runner.py`; pick best impl |
| `isort_formatter.py` | 🟢 MOVE → `mcp_tools_py/formatter/` | merge with existing `isort_runner.py` |
| `config_reader.py` | 🟢 MOVE → `mcp_tools_py/formatter/` | Python-specific (rule #4) |
| `models.py`, `utils.py` | 🟢 MOVE → `mcp_tools_py/formatter/` | follow the formatters they support |

### `icoder/`

| Module | Disposition | Notes |
|---|---|---|
| entire `icoder/` tree | 🔴 KEEP | self-contained TUI app; candidate for own repo *later*, not now |

### `llm/`

| Module | Disposition | Notes |
|---|---|---|
| `env.py`, `interface.py`, `types.py`, `serialization.py` | 🔴 KEEP | |
| `mlflow_*` (4 files) | 🔴 KEEP | mlflow integration |
| `formatting/` (4 files) | 🔴 KEEP | stream renderer, SDK serialization |
| `providers/claude/` (7 files) | 🔴 KEEP | Claude CLI + API provider |
| `providers/langchain/` (10 files) | 🔴 KEEP | multi-backend LangChain provider |
| `session/resolver.py` | 🔴 KEEP | |
| `storage/session_*.py` | 🔴 KEEP | |

### `prompts/`

| Module | Disposition | Notes |
|---|---|---|
| `prompts.md`, `prompt_instructions.md`, `prompts_testdata.md` | 🔴 KEEP | project prompt assets |

### `utils/`

Re-audited under rules #3 and #4. Many previous 🟢 MOVE rows are now 🔴 KEEP because only `mcp_coder` uses them.

| Module | Disposition | Notes |
|---|---|---|
| `clipboard.py` | 🔴 KEEP | mcp_coder-only; candidate for deletion |
| `crash_logging.py` | 🔴 KEEP | mcp_coder-only for now |
| `data_files.py` | 🔴 KEEP | mcp_coder-only |
| `folder_deletion.py` | 🔴 KEEP | mcp_coder-only |
| `git_utils.py` | 🔴 KEEP | workflow-aware; primitives live in `mcp_workspace` instead |
| `log_utils.py` | 🟢 MOVE | → mcp-utils (used by all servers, has redaction logic others lack) |
| `mlflow_config_loader.py` | 🔴 KEEP | mlflow-specific |
| `pyproject_config.py` | 🟢 SPLIT | `get_formatter_config` + `check_line_length_conflicts` → `mcp_tools_py/formatter/`; `get_github_install_config` + `GitHubInstallConfig` stay in mcp_coder (install-from-github CLI feature) |
| `subprocess_runner.py` | 🟢 MOVE | → mcp-utils (canonical; replaces copies in all servers) |
| `subprocess_streaming.py` | 🟢 MOVE | → mcp-utils (pairs with `subprocess_runner`) |
| `timezone_utils.py` | 🔴 KEEP | mcp_coder-only |
| `user_config.py` | 🔴 KEEP | mcp_coder-only |

### `utils/git_operations/`

Entire package moves to `mcp_workspace`. Rationale: git state *is* workspace state; consolidating all git in one server matches rule #2 (one server per domain). mcp_coder's workflow logic continues to exist, but calls git via MCP instead of importing directly.

| Module | Disposition | Notes |
|---|---|---|
| `core.py` | 🟢 MOVE → `mcp_workspace` | low-level `_run_git` runner |
| `branches.py`, `branch_queries.py` | 🟢 MOVE → `mcp_workspace` | |
| `commits.py`, `diffs.py`, `compact_diffs.py` | 🟢 MOVE → `mcp_workspace` | |
| `file_tracking.py`, `staging.py`, `remotes.py` | 🟢 MOVE → `mcp_workspace` | |
| `parent_branch_detection.py` | 🟢 MOVE → `mcp_workspace` | |
| `repository_status.py`, `workflows.py` | 🟢 MOVE → `mcp_workspace` | workflow-aware, but still pure git — exposed as MCP tools, called by mcp_coder workflows |

### `utils/github_operations/`

Under rule #1 (MCP-first), the **mechanics** of talking to GitHub move out of mcp_coder. **For now they go into `mcp_workspace`** as a new `file_tools/github_operations.py` module, rather than spinning up a dedicated `mcp_github` repo. A future split into its own server remains possible (see §6).

The **policy** (when/why to create PRs, which labels to apply) stays in mcp_coder workflows.

| Module | Disposition | Notes |
|---|---|---|
| `base_manager.py`, `github_utils.py` | 🟢 MOVE → `mcp_workspace` | low-level GitHub API access |
| `pr_manager.py` | 🟢 MOVE → `mcp_workspace` | PR CRUD becomes MCP tools |
| `labels_manager.py`, `label_config.py` | 🟢 MOVE → `mcp_workspace` | label CRUD as MCP tools; `labels.json` config stays in mcp_coder |
| `ci_results_manager.py` | 🟢 MOVE → `mcp_workspace` | CI run/artifact reads as MCP tools |
| `issues/` subpackage (all 9 files) | 🟢 MOVE → `mcp_workspace` | issue CRUD, branch_manager, cache, mixins — all API mechanics |
| **Exception: workflow policy** | 🔴 KEEP | anything in mcp_coder's workflows that *decides* (e.g. "set label X when CI passes") stays; only the *call* moves |

### `utils/jenkins_operations/`

| Module | Disposition | Notes |
|---|---|---|
| `client.py`, `models.py` | 🟡 TBD → future `mcp_jenkins` | same pattern as GitHub, but deferred; stays in mcp_coder until the new server is built |

### `workflows/`

| Module | Disposition | Notes |
|---|---|---|
| `utils.py` | 🔴 KEEP | |
| `create_plan/` | 🔴 KEEP | |
| `create_pr/` | 🔴 KEEP | |
| `implement/` | 🔴 KEEP | |
| `vscodeclaude/` (11 files) | 🔴 KEEP | VS Code coordinator workflow |

### `workflow_utils/`

| Module | Disposition | Notes |
|---|---|---|
| `base_branch.py`, `commit_operations.py`, `failure_handling.py`, `task_tracker.py` | 🔴 KEEP | tied to implement/PR loop |

---

## 3. `mcp_tools_py` (reference repo — MCP server for code checks)

### Top-level

| Module | Disposition | Notes |
|---|---|---|
| `main.py`, `server.py`, `__init__.py` | 🔴 KEEP | MCP server entry |
| `checker_tools.py` | 🔴 KEEP | tool registration |
| `utility_tools.py` | 🔴 KEEP | MCP sleep-tool registration (not a utils lib — misnamed). Stays as MCP server feature |
| `inspect_library.py` | 🔴 KEEP | `get_library_source` logic |
| `log_utils.py` | ⚫ CONSOLIDATE | duplicate → use mcp-utils/logging |

### `code_checker_mypy/`, `code_checker_pylint/`, `code_checker_pytest/`, `code_checker_vulture/`

| Module | Disposition | Notes |
|---|---|---|
| all files (models, parsers, reporting, runners, utils) | 🔴 KEEP | domain: code checking |

### `formatter/`

This is the **canonical home** for black/isort runners. mcp_coder's duplicates get deleted and its surrounding files (`config_reader`, `models`, `utils`) land here.

| Module | Disposition | Notes |
|---|---|---|
| `black_runner.py` | 🔴 KEEP (canonical) | absorbs mcp_coder's `black_formatter.py` |
| `isort_runner.py` | 🔴 KEEP (canonical) | absorbs mcp_coder's `isort_formatter.py` |
| `formatter_tools.py` | 🔴 KEEP | MCP tool wrapper |
| *(incoming)* `config_reader.py`, `models.py`, `utils.py` | ✨ NEW (from mcp_coder) | |

### `refactoring/`

| Module | Disposition | Notes |
|---|---|---|
| `jedi_tools.py`, `rope_tools.py`, `rope_cli.py` | 🔴 KEEP | refactoring primitives |

### `utils/`

| Module | Disposition | Notes |
|---|---|---|
| `file_utils.py` | 🟢 MOVE → `mcp-utils/fs/read_file` | identical to p_config's copy; trivial dedupe |
| `project_config.py` | 🔴 KEEP | NOT a duplicate of mcp_coder's `pyproject_config` — reads packaging/test metadata for code checkers. Stays |
| `subprocess_runner.py` | ⚫ CONSOLIDATE | contributes `format_command` + structured logging style to merged mcp-utils version |

---

## 4. `mcp_workspace` (reference repo — MCP server for file ops)

### Top-level

| Module | Disposition | Notes |
|---|---|---|
| `main.py`, `server.py`, `__init__.py` | 🔴 KEEP | MCP server entry |
| `log_utils.py` | ⚫ CONSOLIDATE | → mcp-utils/logging |

### `file_tools/`

| Module | Disposition | Notes |
|---|---|---|
| `directory_utils.py` | 🔴 KEEP | MCP-facing |
| `edit_file.py` | 🔴 KEEP | core edit semantics |
| `file_operations.py` | 🔴 KEEP | MCP-facing |
| `git_operations.py` | 🔴 KEEP (canonical) | **the only home for git-related code.** Absorbs the entirety of `mcp_coder/utils/git_operations/`. Exposed as MCP tools so mcp_coder can call them |
| `path_utils.py` | 🟢 MOVE → `mcp-utils/fs/path_security` | `normalize_path()` path-traversal prevention; separate concern from `read_file` |
| `search.py` | 🔴 KEEP | |
| `github_operations.py` | ✨ NEW | absorbs entirety of `mcp_coder/utils/github_operations/`. Exposed as MCP tools. Temporary home until (if) a dedicated `mcp_github` server is created |

---

## 5. `mcp_config` (reference repo — MCP config CLI)

### `mcp_config/`

| Module | Disposition | Notes |
|---|---|---|
| `main.py`, `cli_utils.py`, `help_system.py`, `output.py`, `errors.py` | 🔴 KEEP | CLI |
| `detection.py`, `discovery.py` | 🔴 KEEP | MCP client discovery |
| `integration.py`, `paths.py`, `servers.py`, `validation.py`, `utils.py` | 🔴 KEEP | domain |

### `mcp_config/clients/`

| Module | Disposition | Notes |
|---|---|---|
| `base.py`, `claude_code.py`, `claude_desktop.py`, `intellij.py`, `vscode.py`, `constants.py`, `utils.py` | 🔴 KEEP | client-specific handlers |

### `src/utils/` (top-level in this repo)

| Module | Disposition | Notes |
|---|---|---|
| `file_utils.py` | 🟢 MOVE → `mcp-utils/fs/read_file` | identical to p_tools's copy; trivial dedupe |
| `subprocess_runner.py` | ⚫ CONSOLIDATE | older/simpler; reference only, not canonical source |

*(The earlier "→ mcp_workspace (under consideration)" block is removed: the decision is now made and documented in §2 under `utils/git_operations/` and `utils/github_operations/`.)*

---

## 6. `mcp_github` — possible future (for illustration)

**Not an action item.** Documented here only to show that the GitHub code landing in `mcp_workspace` can later be split out if/when the scope justifies it. No work planned.

**Trigger to revisit:** if `mcp_workspace/file_tools/github_operations.py` grows large enough (many subfiles, heavy API surface) that it stops fitting the "workspace" concept.

**Rule-of-thumb boundary, for that eventual split:**

- **Into a future `mcp_github`:** anything that talks to `api.github.com`, `gh` CLI, or a GitHub webhook payload.
- **Stays in `mcp_coder`:** anything that decides *when* or *why* to call GitHub (label transitions, PR-creation triggers, coordinator logic).

---

## Cross-cutting decisions still open

1. **Release coupling** — bumping mcp-utils means bumping all downstream repos. Acceptable, or push toward monorepo?
2. **`subprocess_runner` canonical merge** — mcp_coder and p_tools have *different* feature supersets (mcp_coder: heartbeat, launch_process, env_remove, get_utf8_env; p_tools: format_command, cleaner structured logging). Canonical version must merge both, not pick one. Scheduled for phase 2 execution.

*(Resolved during Phase 0 — see "Phase 0 findings" below. Earlier resolved: log_utils canonical choice = mcp_coder, formatters routing = mcp_tools_py, git primitives = mcp_workspace, mcp-llm deferred, icoder deferred.)*

## Phase 0 findings

Pre-work completed. Key corrections to earlier plan assumptions:

1. **`pyproject_config` and `project_config` are NOT duplicates.** Different files reading different TOML sections for different purposes.
   - `mcp_coder/utils/pyproject_config.py` → **split**: `get_formatter_config` + `check_line_length_conflicts` move to `mcp_tools_py/formatter/`; `get_github_install_config` + `GitHubInstallConfig` **stay in mcp_coder** (mcp_coder-specific install-from-github CLI feature).
   - `mcp_tools_py/utils/project_config.py` → **stays in mcp_tools_py**, untouched. Reads `[tool.setuptools.packages.find]` / `[tool.pytest.ini_options]` — used by code checkers to discover src/test dirs.
2. **`file_utils` and `path_utils` are NOT the same either.**
   - `p_tools/utils/file_utils.py` ≡ `p_config/src/utils/file_utils.py` — literally identical 30-line `read_file()` helper. Trivial dedupe.
   - `p_workspace/file_tools/path_utils.py` — 70-line `normalize_path()` security helper (path traversal prevention). Different responsibility.
   - **Two separate mcp-utils modules, not one merged one:** `fs/read_file.py` (from the two duplicates) + `fs/path_security.py` (from p_workspace).
3. **`utility_tools.py` is an MCP sleep-tool registration**, not a utils library. Misnamed. **Stays in mcp_tools_py** 🔴 KEEP. Optional rename to `sleep_tool.py` out of scope.
4. **`log_utils` canonical = mcp_coder's version.** Clear superset: custom OUTPUT log level (25), CleanFormatter for CLI, testing-env detection, redaction support via `_redact_for_logging`, `log_function_call` with `sensitive_fields` parameter. Server versions (p_tools, p_workspace) are much smaller and lack all of these. Servers upgrade by adopting mcp_coder's.
5. **`subprocess_runner` canonical = merge mcp_coder + p_tools.** Not a simple pick. Three-way drift:
   - mcp_coder: heartbeat, launch_process, env_remove, get_utf8_env, FileNotFoundError/PermissionError branches
   - p_tools: format_command helper, cleaner structured logging via `extra={}`
   - p_config: older, simpler — reference only
   - Canonical: mcp_coder as base + absorb p_tools's `format_command` + adopt p_tools's logging style. Merge work happens in phase 2.
6. **Phase-2 coupling check: clean.** `subprocess_runner` uses only stdlib. `subprocess_streaming` depends only on `.subprocess_runner` (must move together). `log_utils` depends on `structlog` + `python-json-logger` (pip packages), zero internal imports. All three safe to move.
7. **Deferred to just-in-time (per-phase) validation:** source-read validation for phase 4 (formatters, pyproject_config split) and phase 5 (git, github). Do not front-load.

---

## Summary counts (mcp_coder)

- 🟢 MOVE → mcp-utils: 3 files (`log_utils.py`, `subprocess_runner.py`, `subprocess_streaming.py`)
- 🟢 MOVE → mcp_tools_py: entire `formatters/` directory + `pyproject_config.py`
- 🟢 MOVE → mcp_workspace: entire `utils/git_operations/` + entire `utils/github_operations/` (~30 files)
- 🔴 KEEP: cli, workflows, llm, icoder, checks, jenkins_operations, workflow_utils, prompts, config, and most of `utils/` (clipboard, crash_logging, data_files, folder_deletion, timezone_utils, user_config, mlflow_*, git_utils)

## General overview / architecture / relationship of 5 repos

Imports flow **downward**: top-level consumers → shared library at the bottom.

```
┌──────────────┐   ┌────────────────┐   ┌──────────────┐   ┌──────────────┐
│  mcp_coder   │   │  mcp_tools_py  │   │ mcp_workspace│   │  mcp_config  │
│  CLI + wf    │   │  MCP server:   │   │  MCP server: │   │  CLI: MCP    │
│  + LLM + TUI │   │  checks/fmt/   │   │  file ops    │   │  client cfg  │
│              │   │  refactoring   │   │              │   │              │
└──────┬───────┘   └────────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                    │                  │                  │
       │ (runtime, via MCP) │                  │                  │
       ├───────────────────▶│                  │                  │
       ├───────────────────────────────────────▶                  │
       │                    │                  │                  │
       │ (all four import at build-time)                          │
       ▼                    ▼                  ▼                  ▼
                      ┌────────────────┐
                      │   mcp-utils    │  (NEW, leaf — no internal deps)
                      │   library      │
                      └────────────────┘
```

**Decided:** all of `mcp_coder`'s `git_operations/` and `github_operations/` move into `mcp_workspace`. Git goes into the existing `file_tools/git_operations.py` (canonical home). GitHub goes into a new `file_tools/github_operations.py`. A dedicated `mcp_github` server remains possible future (§6).

**Roles:**

- **mcp_coder** — end-user CLI; orchestrates workflows (implement, create_pr, coordinator), hosts LLM providers, icoder TUI. Consumer of everything.
- **mcp_tools_py** — MCP server exposing code-quality tools (pylint, mypy, pytest, vulture, black, isort) and refactoring (jedi, rope). Called by Claude via MCP.
- **mcp_workspace** — MCP server exposing file read/edit/search/move tools. Called by Claude via MCP.
- **mcp_config** — standalone CLI to install/manage MCP server entries in Claude Code / Desktop / VS Code / IntelliJ config files.
- **mcp-utils** *(new)* — pure Python library of low-level helpers. Leaf in the graph: depends on nothing internal; everything else depends on it.

## What to move from mcp-coder to tools-py and to workspace

Orthogonal to mcp-utils: some mcp_coder code belongs in the MCP servers, not in a shared library.

**Background — formatters are the odd one out.** `mcp_coder` already calls `pylint`, `mypy`, `pytest`, `vulture` via the `mcp_tools_py` MCP server — it has no local runners for those. The only code-tool runners still living in `mcp_coder` are `formatters/black_formatter.py` and `formatters/isort_formatter.py`. Fix: treat them like the others — delete the local copies and call `mcp_tools_py`'s `formatter/black_runner.py` + `isort_runner.py` via MCP. This is the pattern, not an exception.

### → `mcp_tools_py`

| Source in mcp_coder | Rationale |
|---|---|
| `formatters/black_formatter.py` | Route via MCP, same as pylint/mypy/pytest/vulture already do. Delete local copy |
| `formatters/isort_formatter.py` | same |
| `formatters/config_reader.py`, `models.py`, `utils.py` | follow the formatters they support — move or delete alongside |
| `checks/file_sizes.py` | generic repo check, no GitHub coupling — could become an MCP tool |

### → `mcp_workspace`

| Source in mcp_coder | Rationale |
|---|---|
| entire `utils/git_operations/` | canonical home for all git-related code (rule #2: one server per domain) |
| entire `utils/github_operations/` | lands in new `file_tools/github_operations.py`; temporary home until the possible future `mcp_github` split |

### Stays in mcp_coder

- `checks/branch_status.py`, `checks/ci_log_parser.py` — GitHub/PR workflow policy (decides *when*, not *how*)
- `utils/jenkins_operations/` — deferred; moves to its own future server (§0)
- `utils/git_utils.py` — workflow-aware helpers that call git primitives (now via MCP)

## General guidelines for consolidating / moving code

1. **Only move what has ≥2 real consumers** — or is provably generic. A single-user "might be useful" module stays where it is.
2. **One canonical name per concept** — resolve `pyproject_config` vs `project_config`, `file_utils` vs `path_utils` *before* moving, not after.
3. **Moved modules must be leaf code** — no imports from `mcp_coder.*`, `mcp_tools_py.*`, etc. If a helper pulls in project-specific types, it's not ready to move.
4. **Move tests with the code** — each moved module brings its unit tests to the new repo. Integration tests stay with the consumer.
5. **Pick the best implementation, don't merge** — when 3 repos have `subprocess_runner.py`, choose one (usually the most featureful) and delete the others. Do not try to union APIs.
6. **Order of operations per module:**
   1. Land the module in mcp-utils with tests (new repo PR)
   2. Release a version tag
   3. Update each consumer repo in its own PR: bump dep, swap imports, delete local copy
   4. Never leave two copies live across releases
7. **Start with leaf modules** — `subprocess_runner` + `log_utils` first (pure mcp-utils moves). Then `formatters/` → mcp_tools_py. Then `pyproject_config` consolidation. Then the bigger git/github moves into mcp_workspace last.
8. **Preserve public API on move** — keep function names/signatures identical so consumer updates are mechanical (`from mcp_coder.utils.x import y` → `from mcp_utils.x import y`).
9. **No deprecation shims** — we control all 4 consumers. Atomic swap per module; no `mcp_coder.utils.subprocess_runner` re-export left behind.
10. **One PR per module per repo** — keeps diffs reviewable and rollback cheap. Don't batch "move 8 modules" into one PR.

### Planning and implementation process (cross-repo work)

We use issues + PRs per repo. There is no cross-repo PR mechanism on GitHub, so coordination is manual. Proposed approach:

1. **Tracking issue lives in `mcp_coder`** — it is the primary consumer and the repo you work in daily. Each move gets one tracking issue there titled e.g. `extract: subprocess_runner → mcp-utils`. This issue holds the plan, the repo-by-repo checklist, and the links to all child PRs.
2. **Per-repo issues are thin** — each downstream repo (`mcp_tools_py`, `mcp_workspace`, `mcp_config`, `mcp-utils`) gets a short issue that links back to the tracking issue. No duplicated context.
3. **PR sequence is strict and serial** (matches guideline #6 above):
   1. PR on `mcp-utils` — land module + tests. Merge. Tag release.
   2. PR on `mcp_coder` — bump `mcp-utils` dep, swap imports, delete local copy. Merge.
   3. PR on each other consumer (`mcp_tools_py`, `mcp_workspace`, `mcp_config`) — same swap. Merge.
   4. Close the tracking issue only when every consumer is updated and no stale copy remains.
4. **One module per tracking issue** — do not batch `subprocess_runner` and `log_utils` into one effort. Keeps scope small and rollback cheap.
5. **Checklist shape on the tracking issue:**
   - [ ] mcp-utils PR merged + released (`vX.Y.Z`)
   - [ ] mcp_coder PR merged (dep bumped, local copy deleted)
   - [ ] mcp_tools_py PR merged
   - [ ] mcp_workspace PR merged
   - [ ] mcp_config PR merged
   - [ ] Grep all 4 repos: no references to old import path remain
6. **Branch names** — consistent prefix across repos so they're easy to find: `extract/subprocess-runner`, `extract/log-utils`, etc.
7. **Rollback plan** — if a downstream swap breaks, revert that repo's PR only. `mcp-utils` does not need to roll back because old versions remain usable via pin.
