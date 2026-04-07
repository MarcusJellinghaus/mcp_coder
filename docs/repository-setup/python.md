# Python Setup

Python-specific configuration and tooling. Only relevant if your downstream project is a Python project.

## `pyproject.toml`

**Principle:** Include architecture and quality tools in development dependencies.

**Reference:** See `pyproject.toml` in this repository for complete dependency setup including version constraints and optional dependency groups.

## `.python-version`

Pins the Python version used for the repo. Tools like `pyenv` and `uv` read this file.

## Architecture Enforcement

Enforce module boundaries and prevent architectural drift with automated tools. These components help maintain code quality and keep files manageable for LLM context windows.

### Why Architecture Enforcement?

**Critical for LLM-assisted development workflows:**

**Context Window Management:**
- **File size limits**: LLMs have finite context windows - large files reduce available context for reasoning
- **Architecture enforcement**: LLMs may not grasp the full codebase - rules enforce following a testable architecture plan with clear boundaries, separation of concerns, and clean code that improves LLM comprehension and prevents technical debt

**CI Integration Strategy:**
- **Matrix execution with fail-fast disabled**: Get complete feedback on all checks simultaneously
- **PR-only validation**: Expensive architecture checks run only when needed
- **Comprehensive monitoring**: Use `mcp-coder check branch-status` for complete CI pipeline visibility

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

**For Claude Code**, use MCP tools instead of shell scripts:
- `mcp__tools-py__run_format_code` (replaces `format_all.sh`)
- `mcp__tools-py__run_lint_imports_check` (replaces `lint_imports.sh`)
- `mcp__tools-py__run_vulture_check` (replaces `vulture_check.sh`)

### Import Architecture Enforcement

**Tool: import-linter**
- **Purpose:** Contract-based import validation
- **Execution:** `./tools/lint_imports.sh` (Linux/macOS) or `tools\lint_imports.bat` (Windows)
- **Direct:** `lint-imports`
- **Documentation:** [import-linter docs](https://import-linter.readthedocs.io/)
- **Example config:** See `.importlinter` in this repository

### Dependency Architecture Validation

**Tool: tach**
- **Purpose:** Architectural boundary enforcement
- **Execution:** `./tools/tach_check.sh` (Linux/macOS) or `tools\tach_check.bat` (Windows)
- **Direct:** `tach check`
- **Documentation:** [tach docs](https://docs.gauge.so/tach/)
- **Example config:** See `tach.toml` in this repository

**Tool: pycycle**
- **Purpose:** Circular dependency detection
- **Execution:** `./tools/pycycle_check.sh` (Linux/macOS) or `tools\pycycle_check.bat` (Windows)
- **Direct:** `pycycle --here`
- **Documentation:** [pycycle PyPI](https://pypi.org/project/pycycle/)

### Dead Code Elimination

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

| Script | Purpose | Category |
|--------|---------|----------|
| `format_all.sh/bat` | Run black + isort on src/tests | **Mandatory** before commits |
| `black.bat` | Run black formatter only | Optional |
| `iSort.bat` | Run isort only | Optional |
| `ruff_check.sh/bat` | Run ruff (docstring checks) | Optional |

> **For Claude Code:** Use `mcp__tools-py__run_format_code` (runs both isort and black).
> Shell scripts are for human developers and CI pipelines.

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

### Utility Tools

| Script | Purpose | Category |
|--------|---------|----------|
| `checks2clipboard.bat` | Copy quality check output to clipboard | Optional, useful for LLM assistance |

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
