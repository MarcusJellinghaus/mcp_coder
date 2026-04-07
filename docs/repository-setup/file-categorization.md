# File Categorization Review

Working document for assigning every file/folder to a category. **This file is for review and will not be committed as final docs.**

## Categories

- **G** = General — any downstream repo using mcp-coder
- **P** = Python — only relevant if downstream is a Python project
- **I** = Internal — mcp-coder repo itself, not for downstream users
- **L** = Legacy / to-be-reviewed
- **?** = Needs your decision

## Status legend

- `ok`  = Confirmed in discussion
- `new` = Proposed by Claude (please review)
- `?`   = Open question

---

## Root files

| File                       | Cat | Status | Reasoning                                          |
|----------------------------|-----|--------|----------------------------------------------------|
| `README.md`                | G   | new    | Standard project README                            |
| `.gitignore`               | G   | ok     | Centralized list — already in repo.md              |
| `.gitattributes`           | G   | ok     | Line endings — language-agnostic                   |
| `.mcp.json`                | G   | ok     | MCP server config — language-agnostic              |
| `.python-version`          | P   | ok     | Python version pin                                 |
| `pyproject.toml`           | P   | new    | Python project config (move to python.md)          |
| `requirements-beta.txt`    | L   | ok     |                                                    |
| `.importlinter`            | P   | new    | Python import contracts (move to python.md)       |
| `tach.toml`                | P   | new    | Python module boundaries (move to python.md)       |
| `vulture_whitelist.py`     | P   | new    | Python dead code (move to python.md)               |
| `.large-files-allowlist`   | G   | new    | mcp-coder file-size feature, language-agnostic     |
| `claude.bat`               | G   | ok     | Claude launcher — language-agnostic                |
| `claude_local.bat`         | G   | ok     | Claude launcher (local venv) — language-agnostic   |
| `icoder.bat`               | I   | ok     | icoder command launcher (mcp-coder repo only)      |
| `icoder_local.bat`         | I   | ok     | icoder launcher (local venv, mcp-coder repo only)  |
| `mlflow_implementation.md` | I   | ok     | Design doc for mcp-coder's mlflow integration      |
| `project_idea.md`          | I   | ok     | Design notes for mcp-coder itself                  |
| `.run/`                    | I   | new    | IntelliJ/PyCharm IDE run configurations            |

---

## `.github/`

| File                                          | Cat | Status | Reasoning                                                |
|-----------------------------------------------|-----|--------|----------------------------------------------------------|
| `.github/dependabot.yml`                      | G   | ok     | Already in github.md                                     |
| `.github/workflows/label-new-issues.yml`      | G   | ok     | Already in github.md                                     |
| `.github/workflows/approve-command.yml`       | G   | ok     | Already in github.md                                     |
| `.github/workflows/ci.yml`                    | P   | ok     | General structure in github.md, Python matrix in python.md |
| `.github/workflows/langchain-integration.yml` | I   | new    | Tests mcp-coder's own langchain integration              |
| `.github/workflows/publish.yml`               | I   | new    | Publishes mcp-coder package to PyPI                      |

---

## `.claude/`

| File / Folder                                              | Cat | Status | Reasoning                                       |
|------------------------------------------------------------|-----|--------|-------------------------------------------------|
| `.claude/CLAUDE.md`                                        | G   | ok     | Already in claude-code.md                       |
| `.claude/settings.local.json`                              | G   | ok     | Already in claude-code.md                       |
| `.claude/agents/commit-pusher.md`                          | G   | new    | Workflow agent referenced by skills             |
| `.claude/knowledge_base/planning_principles.md`            | G   | new    | Referenced by skills                            |
| `.claude/knowledge_base/python.md`                         | P   | new    | Python-specific knowledge for code review       |
| `.claude/knowledge_base/refactoring_principles.md`         | G   | new    | Referenced by skills                            |
| `.claude/knowledge_base/software_engineering_principles.md`| G   | new    | Referenced by skills                            |
| `.claude/skills/check_branch_status/SKILL.md`              | G   | new    | Generic workflow skill                          |
| `.claude/skills/commit_push/SKILL.md`                      | G   | new    | Generic workflow skill                          |
| `.claude/skills/discuss/SKILL.md`                          | G   | new    | Generic discussion skill                        |
| `.claude/skills/implement_direct/SKILL.md`                 | G   | new    | Generic workflow skill                          |
| `.claude/skills/implementation_approve/SKILL.md`           | G   | new    | Generic workflow skill                          |
| `.claude/skills/implementation_finalise/SKILL.md`          | G   | new    | Generic workflow skill                          |
| `.claude/skills/implementation_needs_rework/SKILL.md`      | G   | new    | Generic workflow skill                          |
| `.claude/skills/implementation_new_tasks/SKILL.md`         | G   | new    | Generic workflow skill                          |
| `.claude/skills/implementation_review/SKILL.md`            | G   | new    | Generic code review skill                       |
| `.claude/skills/implementation_review_supervisor/SKILL.md` | G   | new    | Generic code review skill                       |
| `.claude/skills/issue_analyse/SKILL.md`                    | G   | new    | Generic issue workflow                          |
| `.claude/skills/issue_approve/SKILL.md`                    | G   | new    | Generic issue workflow                          |
| `.claude/skills/issue_create/SKILL.md`                     | G   | new    | Generic issue workflow                          |
| `.claude/skills/issue_requirements/SKILL.md`               | G   | new    | Generic issue workflow                          |
| `.claude/skills/issue_update/SKILL.md`                     | G   | new    | Generic issue workflow                          |
| `.claude/skills/plan_approve/SKILL.md`                     | G   | new    | Generic plan workflow                           |
| `.claude/skills/plan_review/SKILL.md`                      | G   | new    | Generic plan workflow                           |
| `.claude/skills/plan_review_supervisor/SKILL.md`           | G   | new    | Generic plan workflow                           |
| `.claude/skills/plan_update/SKILL.md`                      | G   | new    | Generic plan workflow                           |
| `.claude/skills/rebase/SKILL.md`                           | G   | new    | Generic git workflow                            |
| `.claude/skills/rebase/rebase_design.md`                   | G   | new    | Design doc for rebase skill                     |

---

## `tools/` — Python-specific (would go in `python.md`)

| File                                | Cat | Status | Reasoning                                    |
|-------------------------------------|-----|--------|----------------------------------------------|
| `tools/format_all.sh` / `.bat`      | P   | new    | Runs black + isort                           |
| `tools/black.bat`                   | P   | new    | Black formatter                              |
| `tools/iSort.bat`                   | P   | new    | isort                                        |
| `tools/lint_imports.sh` / `.bat`    | P   | new    | import-linter wrapper                        |
| `tools/tach_check.sh` / `.bat`      | P   | new    | tach wrapper                                 |
| `tools/pycycle_check.sh` / `.bat`   | P   | new    | Python circular dependency check             |
| `tools/vulture_check.sh` / `.bat`   | P   | new    | vulture wrapper                              |
| `tools/pylint_check_for_errors.bat` | P   | new    | pylint wrapper                               |
| `tools/mypy.bat`                    | P   | new    | mypy wrapper                                 |
| `tools/ruff_check.sh` / `.bat`      | P   | new    | ruff wrapper (missing from code-quality.md)  |
| `tools/pydeps_graph.sh` / `.bat`    | P   | new    | Python dependency graph generator            |
| `tools/tach_docs.sh` / `.bat` / `.py` | P | new    | Architecture doc generator from tach         |
| `tools/get_pytest_performance_stats.bat` | P | new  | pytest performance stats                     |
| `tools/test_profiler.bat`           | P   | new    | pytest profiler                              |
| `tools/test_profiler_generate_only.bat` | P | new  | pytest profiler reports                      |
| `tools/test_profiler.md`            | P   | new    | Documents test_profiler.bat                  |
| `tools/test_profiler_plugin/`       | P   | new    | pytest plugin code                           |
| `tools/checks2clipboard.bat`        | P   | new    | Copies Python check output to clipboard      |

---

## `tools/` — Internal (mcp-coder repo only)

| File                                  | Cat | Status | Reasoning            |
|---------------------------------------|-----|--------|----------------------|
| `tools/reinstall_local.bat`           | I   | ok     |                      |
| `tools/read_github_deps.py`           | I   | ok     |                      |
| `tools/safe_delete_folder.py`         | I   | ok     |                      |
| `tools/get_latest_mlflow_db_entries.py` | I | ok     | mlflow group         |
| `tools/get_mlflow_config.py`          | I   | ok     | mlflow group         |
| `tools/get_recent_mlflow_runs.py`     | I   | ok     | mlflow group         |
| `tools/inspect_mlflow_run.py`         | I   | ok     | mlflow group         |
| `tools/search_mlflow_artifacts.py`    | I   | ok     | mlflow group         |
| `tools/start_mlflow.sh` / `.bat`      | I   | ok     | mlflow group         |
| `tools/__init__.py`                   | I   | new    | Makes tools/ a package |

---

## `tools/` — Legacy / to-be-reviewed

| File                            | Cat | Status | Reasoning                          |
|---------------------------------|-----|--------|------------------------------------|
| `tools/check_version.bat`       | L   | ok     |                                    |
| `tools/test_prompt.bat`         | L   | ok     |                                    |
| `tools/docstring_stats.sh`      | L   | ok     |                                    |
| `tools/debug_vscode_sessions.py`| L   | ok     |                                    |
| `tools/debug_windows.py`        | L   | ok     |                                    |
| `tools/commit_summary.bat`      | L   | new    | Already labeled "Legacy"           |
| `tools/pr_summary.bat`          | L   | new    | Already labeled "Legacy"           |
| `tools/pr_review.bat`           | L   | new    | Already labeled "Legacy"           |
| `tools/pr_review_highlevel.bat` | L   | new    | Already labeled "Legacy"           |

---

## Counts (after your review)

- **G** (General): ~30 files (skills, knowledge base, .claude config, .gitignore, .gitattributes, .mcp.json, dependabot, 2 GH actions, claude launchers)
- **P** (Python): ~30 files (linting/formatting tools, .importlinter, tach.toml, vulture, pyproject.toml, .python-version, ci.yml maybe)
- **I** (Internal): ~13 files (mlflow tools, reinstall, design docs, internal CI workflows, .run)
- **L** (Legacy): ~10 files (deprecated batch scripts, requirements-beta.txt)
