# mcp-utils Extraction Plan — Module Inventory

Planning doc for introducing a shared `mcp-utils` repo across the 4 existing repos.
Every module in every repo is listed below with a proposed disposition. Nothing is final — this is the working surface for decisions.

**Legend:**

- 🟢 **MOVE** — move to `mcp-utils`
- 🔴 **KEEP** — stays in current repo (domain-specific)
- 🟡 **TBD** — needs discussion
- ⚫ **CONSOLIDATE** — duplicate of another repo's module; pick one source of truth
- ✨ **NEW** — new module in `mcp-utils`

---

## 1. `mcp-utils` (NEW repo — proposed)

Target shape. Populated by moves from the other four repos.

| Module | Source | Notes |
|---|---|---|
| `subprocess/runner` | ✨ from mcp_coder + mcp_tools_py + mcp_config | 3 duplicate implementations — pick best |
| `subprocess/streaming` | ✨ from mcp_coder | streaming variant, mcp_coder-only today |
| `logging/log_utils` | ✨ from mcp_coder + mcp_tools_py + mcp_workspace | 3 duplicates; mcp_coder has redaction |
| `config/pyproject_config` | ✨ from mcp_coder + mcp_tools_py | pyproject.toml reader |
| `config/user_config` | ✨ from mcp_coder | generic `~/.config` TOML loader |   TODO - not sure whether we need this in the other repos
| `fs/data_files` | ✨ from mcp_coder | packaged-data file access |        TODO - not sure whether we need this in the other repos
| `fs/folder_deletion` | ✨ from mcp_coder | safe recursive delete |     TODO - not sure whether we need this in the other repos
| `fs/file_utils` | ✨ from mcp_tools_py + mcp_config | path helpers |
| `git/core` | ✨ from mcp_coder (utils/git_operations/core.py) | low-level `_run_git` only |
| `platform/clipboard` | ✨ from mcp_coder | |  TO BE REVIEWED, leave it whereit is, we migth want to delete this
| `platform/timezone_utils` | ✨ from mcp_coder | |    TODO - not sure whether we need this in the other repos
| `platform/crash_logging` | ✨ from mcp_coder | faulthandler helper |  TODO - new - to be evaluated furst
| `formatter/black_runner` | 🟡 from mcp_tools_py OR mcp_coder | see duplication note below |
| `formatter/isort_runner` | 🟡 from mcp_tools_py OR mcp_coder | see duplication note below |

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

| Module | Disposition | Notes |
|---|---|---|
| `black_formatter.py` | ⚫ CONSOLIDATE | mcp_tools_py has its own black_runner — pick one |
| `isort_formatter.py` | ⚫ CONSOLIDATE | same |
| `config_reader.py` | 🟡 TBD | may fold into mcp-utils/config |
| `models.py`, `utils.py` | 🟡 TBD | |

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
| **Note** | | Entire `llm/` is a future candidate for its own `mcp-llm` repo — flag for later |

### `prompts/`

| Module | Disposition | Notes |
|---|---|---|
| `prompts.md`, `prompt_instructions.md`, `prompts_testdata.md` | 🔴 KEEP | project prompt assets |

### `utils/`

| Module | Disposition | Notes |
|---|---|---|
| `clipboard.py` | 🟢 MOVE | → mcp-utils/platform |
| `crash_logging.py` | 🟢 MOVE | → mcp-utils/platform |
| `data_files.py` | 🟢 MOVE | → mcp-utils/fs |
| `folder_deletion.py` | 🟢 MOVE | → mcp-utils/fs |
| `git_utils.py` | 🟡 TBD | may split: primitives to utils, workflow bits stay |
| `log_utils.py` | 🟢 MOVE | → mcp-utils/logging (incl. redaction) |
| `mlflow_config_loader.py` | 🔴 KEEP | mlflow-specific |
| `pyproject_config.py` | 🟢 MOVE | → mcp-utils/config |
| `subprocess_runner.py` | 🟢 MOVE | → mcp-utils/subprocess |
| `subprocess_streaming.py` | 🟢 MOVE | → mcp-utils/subprocess |
| `timezone_utils.py` | 🟢 MOVE | → mcp-utils/platform |
| `user_config.py` | 🟢 MOVE | → mcp-utils/config |

### `utils/git_operations/`

| Module | Disposition | Notes |
|---|---|---|
| `core.py` | 🟡 TBD | the low-level `_run_git` primitive → mcp-utils/git; rest stays |
| `branches.py`, `branch_queries.py` | 🔴 KEEP | |
| `commits.py`, `diffs.py`, `compact_diffs.py` | 🔴 KEEP | |
| `file_tracking.py`, `staging.py`, `remotes.py` | 🔴 KEEP | |
| `parent_branch_detection.py` | 🔴 KEEP | |
| `repository_status.py`, `workflows.py` | 🔴 KEEP | workflow-aware |

### `utils/github_operations/`

| Module | Disposition | Notes |
|---|---|---|
| all (base_manager, ci_results, github_utils, labels, label_config, pr_manager) | 🔴 KEEP | opinionated GitHub workflow |
| `issues/` subpackage (all 9 files) | 🔴 KEEP | |

### `utils/jenkins_operations/`

| Module | Disposition | Notes |
|---|---|---|
| `client.py`, `models.py` | 🔴 KEEP | Jenkins client for specific pipelines |

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
| `utility_tools.py` | 🔴 KEEP | |
| `inspect_library.py` | 🔴 KEEP | `get_library_source` logic |
| `log_utils.py` | ⚫ CONSOLIDATE | duplicate → use mcp-utils/logging |

### `code_checker_mypy/`, `code_checker_pylint/`, `code_checker_pytest/`, `code_checker_vulture/`

| Module | Disposition | Notes |
|---|---|---|
| all files (models, parsers, reporting, runners, utils) | 🔴 KEEP | domain: code checking |

### `formatter/`

| Module | Disposition | Notes |
|---|---|---|
| `black_runner.py` | 🟡 TBD | see duplication with mcp_coder/formatters |
| `isort_runner.py` | 🟡 TBD | same |
| `formatter_tools.py` | 🔴 KEEP | MCP tool wrapper |

### `refactoring/`

| Module | Disposition | Notes |
|---|---|---|
| `jedi_tools.py`, `rope_tools.py`, `rope_cli.py` | 🔴 KEEP | refactoring primitives |

### `utils/`

| Module | Disposition | Notes |
|---|---|---|
| `file_utils.py` | ⚫ CONSOLIDATE | → mcp-utils/fs |
| `project_config.py` | ⚫ CONSOLIDATE | → mcp-utils/config (same as mcp_coder's pyproject_config) |
| `subprocess_runner.py` | ⚫ CONSOLIDATE | → mcp-utils/subprocess |

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
| `git_operations.py` | 🟡 TBD | has own git runner — could consume mcp-utils/git/core |
| `path_utils.py` | 🟡 TBD | possibly overlaps mcp-utils/fs |
| `search.py` | 🔴 KEEP | |

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
| `file_utils.py` | ⚫ CONSOLIDATE | → mcp-utils/fs |
| `subprocess_runner.py` | ⚫ CONSOLIDATE | → mcp-utils/subprocess |

---

## Cross-cutting decisions to make

1. **subprocess_runner** — 3 implementations exist (mcp_coder, mcp_tools_py, mcp_config). Which is canonical? mcp_coder's is most featureful (has streaming sibling).
2. **log_utils** — 3 implementations. mcp_coder's has redaction logic the others lack. Likely canonical.
3. **Formatters duplication** — mcp_coder/formatters vs mcp_tools_py/formatter. Two paths:
   - (a) Move one copy to mcp-utils; both repos depend on it.
   - (b) Delete mcp_coder/formatters; mcp_coder calls mcp_tools_py via MCP (already does for running checks).
4. **git primitives** — extract just `_run_git` to mcp-utils/git/core, or leave everything in mcp_coder? mcp_workspace/file_tools/git_operations.py also has its own — could consume shared.
5. **pyproject_config vs project_config** — same concept, two names. Pick one.
6. **file_utils** — 3 variants (mcp_tools_py, mcp_config, mcp_workspace has path_utils). Need to compare APIs before merging.
7. **Release coupling** — bumping mcp-utils means bumping 4 downstream repos. Acceptable, or push toward monorepo?
8. **Future `mcp-llm` repo** — flag `mcp_coder/llm/` (~25 files) as a future extraction candidate, but explicitly out of scope for this round.
9. **`icoder/`** — same: future candidate, out of scope now.

---

## Summary counts (mcp_coder)

- 🟢 MOVE: ~12 files (utils/* flat files)
- ⚫ CONSOLIDATE: ~2 files (formatters/black + isort)
- 🟡 TBD: ~4 items (git core split, formatters config_reader, formatters models/utils, git_utils.py)
- 🔴 KEEP: everything else (cli, workflows, llm, icoder, checks, github_operations, jenkins_operations, most of git_operations, workflow_utils, prompts, config)

## Gneral overview / architecture / relationship of 5 repos

TODO

## What to move from mcp-coder to tools-py and to workspace

TODO

## General guidelines for consolidating / moving code

TODO
