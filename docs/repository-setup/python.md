# Python Setup

Python-specific configuration and tooling. Only relevant if your target repo is a Python project.

## `pyproject.toml`

> **Customize:** Use as a reference, not a direct copy. Adapt sections to your project's package name, dependencies, and tool configs.

**Principle:** Include architecture and quality tools in development dependencies.

**Reference:** See `pyproject.toml` in this repository for complete dependency setup including version constraints and optional dependency groups.

### Key Sections

The following `pyproject.toml` sections are read by the Python tools; `[tool.mcp-tools-py] formatter` also by mcp-coder's formatting:

| Section | Read by | Purpose |
|---|---|---|
| `[tool.mcp-tools-py] formatter` | mcp-tools-py (`run_format_code` MCP tool and mcp-coder's formatting) | Selects the formatter: `"black"` (isort + black) or `"ruff"` (ruff imports + ruff format). Optional while table detection is unambiguous |
| `[tool.ruff.format]` | `mcp__mcp-tools-py__run_format_code` | ruff format config; selects ruff when `formatter` is unset and `[tool.black]` is absent |
| `[tool.pytest.ini_options]` | `mcp__mcp-tools-py__run_pytest_check`, pytest CLI | Pytest config (markers, options) |
| `[tool.mypy]` | `mcp__mcp-tools-py__run_mypy_check`, mypy CLI | Mypy strict-mode config |
| `[tool.pylint.main]` / `[tool.pylint.messages_control]` | `mcp__mcp-tools-py__run_pylint_check`, pylint CLI | Pylint config |
| `[tool.ruff]` / `[tool.ruff.lint]` | `tools/ruff_check.sh` / `.bat`, `mcp__mcp-tools-py__run_format_code` | Ruff lint + format config |

**`[tool.mcp-coder]` keys** (format switch, prompts, toolkit, setup, install): see [Project config](../configuration/project-config.md).

**Formatting requires a declared formatter.** mcp-coder formats through mcp-tools-py's resolution, the same one the `run_format_code` MCP tool uses: `[tool.mcp-tools-py] formatter`, else `[tool.ruff.format]` vs `[tool.black]`. A `pyproject.toml` that declares a formatter is required — with none, or with both tables and no `formatter` key, every formatting entry point fails before any LLM call. Set [`[tool.mcp-coder] format_code = false`](../configuration/project-config.md) to skip formatting instead. `mcp-coder verify` shows the toolkit's `formatter` item and its other tool items under the Toolkit row. The old `[tool.mcp-coder.implement] format_code` key is no longer read; `verify` flags it as `[ERR]`.

**Other sections** (`[tool.setuptools.*]`, `[tool.setuptools_scm]`, etc.) are standard Python packaging configuration and not specifically used by mcp-coder workflows.

### Prompt Configuration

`[tool.mcp-coder.prompts]`: see [Project config — Prompts](../configuration/project-config.md#prompts).

## `.python-version`

> **Customize:** Pin to your project's Python version.

Pins the Python version used for the repo. Tools like `pyenv` and `uv` read this file.

## Architecture Enforcement

> Overview: see [quality-and-security-checks.md](quality-and-security-checks.md).

Why the architecture is enforced, and which tool guards what: see
[enforcement.md](../architecture/enforcement.md).

### Import Architecture Enforcement

> **Customize (`.importlinter`):** Package names and contract definitions.

### Dependency Architecture Validation

> **Customize (`tach.toml`):** Module boundaries for your package.

### Dead Code Elimination

> **Customize (`vulture_whitelist.py`):** Project-specific false positives.

### Dependency Declaration Hygiene

> **Customize (`[tool.deptry]` in `pyproject.toml`):** The dev-only extras
> (`optional_dependencies_dev_groups`), per-rule ignores and the
> package-to-module name map.

## CI Workflow for Python

> Overview: see [quality-and-security-checks.md](quality-and-security-checks.md).

The general CI workflow structure is documented in [github.md](github.md#code-quality-ci). The matrix items are Python-specific:

| Matrix item | Tool |
|---|---|
| `ruff` | Linter (includes import sorting, `I`) |
| `ruff-format` | Code formatter (`ruff format --check`) |
| `pylint` | Static analysis (errors only) |
| `pytest` | Test runner |
| `mypy` | Static type checker (strict mode) |
| `import-linter` | Import contract validator |
| `tach` | Architectural boundary check |
| `vulture` | Dead code detection |
| `deptry` | Dependency declaration check |

## Development Tools

Convenience scripts for local development. Create a `tools/` directory with these scripts:

### Formatting Tools

Format via `mcp__mcp-tools-py__run_format_code` (formatter chosen by `[tool.mcp-tools-py] formatter`); the CI formatter jobs are the backstop and also cover `tools/`.

### Quality Check Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `ruff_check.sh/bat` | Run ruff lint on src/tests/tools | Optional (CI runs it) |
| `lint_imports.sh/bat` | Run import-linter | Optional (CI runs it) |
| `tach_check.sh/bat` | Run tach architecture check | Optional (CI runs it) |
| `vulture_check.sh/bat` | Check dead code | Optional (CI runs it) |
| `deptry_check.sh/bat` | Check dependency declarations | Optional (CI runs it) |
| `pylint_check_for_errors.bat` | Run pylint errors only | Optional (CI runs it) |
| `mypy.bat` | Run type checking | Optional (CI runs it) |

> **For Claude Code:** Use MCP tools where available: `mcp__mcp-tools-py__run_lint_imports_check`, `mcp__mcp-tools-py__run_tach_check`, `mcp__mcp-tools-py__run_vulture_check`, `mcp__mcp-tools-py__run_deptry_check`, `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`.
> Shell scripts are for human developers and CI pipelines.

### Performance Analysis Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `get_pytest_performance_stats.bat` | Collect test runtime statistics | Optional |
| `test_profiler.bat` | Profile slow tests | Optional |
| `test_profiler_generate_only.bat` | Generate profiler reports | Optional |
| `pydeps_graph.sh/bat` | Generate dependency visualization | Optional |
| `tach_docs.sh/bat/py` | Generate architecture documentation | Optional |

## Knowledge Base

`.claude/knowledge_base/python.md` provides Python-specific knowledge that the code review skills (`/implementation_review`, `/implementation_review_supervisor`) consult during reviews.
