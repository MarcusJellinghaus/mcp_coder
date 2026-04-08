# Python Setup

Python-specific configuration and tooling. Only relevant if your downstream project is a Python project.

## `pyproject.toml`

> **Customize:** Use as a reference, not a direct copy. Adapt sections to your project's package name, dependencies, and tool configs.

**Principle:** Include architecture and quality tools in development dependencies.

**Reference:** See `pyproject.toml` in this repository for complete dependency setup including version constraints and optional dependency groups.

### Key Sections

The following `pyproject.toml` sections are read by the Python MCP tools and/or by mcp-coder itself:

| Section | Read by | Purpose |
|---|---|---|
| `[tool.black]` | `mcp__tools-py__run_format_code`, `tools/black.bat`, `pyproject_config.py` | Black formatter config |
| `[tool.isort]` | `mcp__tools-py__run_format_code`, `tools/iSort.bat`, `pyproject_config.py` | isort config |
| `[tool.pytest.ini_options]` | `mcp__tools-py__run_pytest_check`, pytest CLI | Pytest config (markers, options) |
| `[tool.mypy]` | `mcp__tools-py__run_mypy_check`, mypy CLI | Mypy strict-mode config |
| `[tool.pylint.main]` / `[tool.pylint.messages_control]` | `mcp__tools-py__run_pylint_check`, pylint CLI | Pylint config |
| `[tool.ruff]` / `[tool.ruff.lint]` | `tools/ruff_check.sh` / `.bat` | Ruff lint + format config |
| `[tool.mcp-coder.install-from-github]` | mcp-coder install process (`pyproject_config.py`) | GitHub-based dependency packages (`packages`, `packages-no-deps`) |

**mcp-coder-specific behavior:** [`src/mcp_coder/utils/pyproject_config.py`](../../src/mcp_coder/utils/pyproject_config.py) reads `[tool.black]` and `[tool.isort]` and warns if their `line-length` settings disagree. It also reads `[tool.mcp-coder.install-from-github]` to find packages mcp-coder should install from GitHub source.

**Other sections** (`[tool.setuptools.*]`, `[tool.setuptools_scm]`, etc.) are standard Python packaging configuration and not specifically used by mcp-coder workflows.

## `.python-version`

> **Customize:** Pin to your project's Python version.

Pins the Python version used for the repo. Tools like `pyenv` and `uv` read this file.

## Architecture Enforcement

Enforce module boundaries and prevent architectural drift with automated tools. These components help maintain code quality and keep files manageable for LLM context windows.

### Why Architecture Enforcement?

Large files consume LLM context budget, and architecture rules with clear boundaries enable more focused analysis and prevent technical debt. CI matrix execution with fail-fast disabled gives complete feedback on all checks at once.

### Running Architecture Tools

**Recommended Approach: Use Tools Scripts**

All architecture tools have corresponding scripts in the `tools/` directory that provide:

- **Better UX**: Informative status messages and progress indicators
- **Error handling**: Check if tools are installed and provide helpful installation guidance
- **Consistency**: Standardized output format and argument handling
- **Cross-platform**: Both `.sh` (Linux/macOS) and `.bat` (Windows) versions

**Examples:**

```bash
# Use these (recommended)
./tools/lint_imports.sh
./tools/tach_check.sh
./tools/pycycle_check.sh
./tools/vulture_check.sh

# Instead of direct commands
lint-imports
tach check
pycycle --here
vulture src tests vulture_whitelist.py --min-confidence 60
```

(For Claude Code MCP tool equivalents, see the Quality Check Tools section below.)

### Import Architecture Enforcement

> **Customize (`.importlinter`):** Package names and contract definitions.

**Tool: import-linter**

- **Purpose:** Contract-based import validation
- **Execution:** `./tools/lint_imports.sh` (Linux/macOS) or `tools\lint_imports.bat` (Windows)
- **Direct:** `lint-imports`
- **Documentation:** [import-linter docs](https://import-linter.readthedocs.io/en/stable/)
- **Example config:** See `.importlinter` in this repository

### Dependency Architecture Validation

> **Customize (`tach.toml`):** Module boundaries for your package.

**Tool: tach**

- **Purpose:** Architectural boundary enforcement
- **Execution:** `./tools/tach_check.sh` (Linux/macOS) or `tools\tach_check.bat` (Windows)
- **Direct:** `tach check`
- **Documentation:** [tach docs](https://docs.gauge.sh/)
- **Example config:** See `tach.toml` in this repository

**Tool: pycycle**

- **Purpose:** Circular dependency detection
- **Execution:** `./tools/pycycle_check.sh` (Linux/macOS) or `tools\pycycle_check.bat` (Windows)
- **Direct:** `pycycle --here`
- **Documentation:** [pycycle PyPI](https://pypi.org/project/pycycle/)

### Dead Code Elimination

> **Customize (`vulture_whitelist.py`):** Project-specific false positives.

**Tool: vulture**

- **Purpose:** Unused code detection
- **Execution:** `./tools/vulture_check.sh` (Linux/macOS) or `tools\vulture_check.bat` (Windows)
- **Direct:** `vulture src tests vulture_whitelist.py --min-confidence 60`
- **Documentation:** [vulture docs](https://github.com/jendrikseipp/vulture)
- **Example config:** See `vulture_whitelist.py` in this repository

## CI Workflow for Python

The general CI workflow structure is documented in [github.md](github.md#code-quality-ci). The matrix items are Python-specific:

| Matrix item | Tool |
|---|---|
| `black` | Code formatter (check mode) |
| `isort` | Import sorter (check mode) |
| `pylint` | Static analysis (errors only) |
| `pytest` | Test runner |
| `mypy` | Static type checker (strict mode) |
| `import-linter` | Import contract validator |
| `tach` | Architectural boundary check |
| `pycycle` | Circular dependency detection |
| `vulture` | Dead code detection |

## Development Tools

Convenience scripts for local development. Create a `tools/` directory with these scripts:

### Formatting Tools

> **Note:** These shell scripts are being phased out in favor of the `mcp__tools-py__run_format_code` MCP tool, which runs both isort and black. Prefer the MCP tool for new workflows. Shell scripts are kept for human developers and CI pipelines.

| Script | Purpose | Category |
|--------|---------|----------|
| `format_all.sh/bat` | Run black + isort on src/tests | **Mandatory** before commits |
| `black.bat` | Run black formatter only | Optional |
| `iSort.bat` | Run isort only | Optional |
| `ruff_check.sh/bat` | Run ruff (docstring checks) | Optional |

**format_all.sh:**

```bash
#!/bin/bash
set -e
echo "Running isort..."
isort --profile=black --float-to-top src tests
echo "Running black..."
black src tests
echo "Formatting complete!"
```

For the `[tool.black]` and `[tool.isort]` config items these tools read, see [Key Sections](#key-sections).

### Quality Check Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `lint_imports.sh/bat` | Run import-linter | Optional (CI runs it) |
| `tach_check.sh/bat` | Run tach architecture check | Optional (CI runs it) |
| `pycycle_check.sh/bat` | Check circular dependencies | Optional (CI runs it) |
| `vulture_check.sh/bat` | Check dead code | Optional (CI runs it) |
| `pylint_check_for_errors.bat` | Run pylint errors only | Optional (CI runs it) |
| `mypy.bat` | Run type checking | Optional (CI runs it) |

> **For Claude Code:** Use MCP tools where available: `mcp__tools-py__run_lint_imports_check` (replaces `lint_imports.sh`), `mcp__tools-py__run_vulture_check` (replaces `vulture_check.sh`), `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`.
> Shell scripts are for human developers and CI pipelines. `tach_check.sh` and `pycycle_check.sh` have no MCP equivalents — run them via Bash when needed.

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
