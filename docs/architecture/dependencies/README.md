# Dependency Management

Tools for enforcing architectural boundaries and detecting dependency issues.

## Tools

| Tool | Purpose | Config | Script |
|------|---------|--------|--------|
| **import-linter** | Enforce import rules (layers, isolation, forbidden) | `.importlinter` | `tools/lint_imports.sh` |
| **tach** | Module boundaries & layer enforcement | `tach.toml` | `tools/tach_check.sh` |
| **pycycle** | Detect circular imports | - | `tools/pycycle_check.sh` |
| **pydeps** | Visualize dependencies | - | `tools/pydeps_graph.bat` |

## Why Both import-linter and tach?

| Feature | import-linter | tach |
|---------|---------------|------|
| Layer enforcement | ✅ | ✅ |
| Third-party isolation | ✅ `forbidden` contracts | ❌ |
| Submodule boundaries | ✅ `independence` contracts | ❌ (struggles with `__init__.py`) |
| Circular dependency detection | ❌ | ✅ |
| Explicit `depends_on` | ❌ | ✅ |

**Summary**: Use both - tach for high-level layers, import-linter for fine-grained rules.

## Running Checks

```bash
# All checks
./tools/lint_imports.sh && ./tools/tach_check.sh && ./tools/pycycle_check.sh

# Individual
lint-imports          # 19 contracts
tach check            # Layer violations
pycycle --here        # Circular imports
```

## Current Contracts (import-linter)

**Architecture (6)**: Layered architecture, domain independence, formatter independence, external services independence, git local isolation, jenkins isolation

**Third-party (11)**: github, git, jenkins, claude_code_sdk, pyperclip, mcp_code_checker, requests, structlog, pythonjsonlogger, black, isort

**Tests (2)**: No test imports in source, test module independence

> Each rule includes comments explaining its rationale. See `.importlinter` and `tach.toml` for details.

## Generated Files

- `dependency_graph.html` - Interactive dependency visualization
- `dependency_report.html` - Tach dependency report  
- `pydeps_graph.html` - Pydeps visualization
