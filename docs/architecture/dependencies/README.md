# Dependency Management

Tools for enforcing architectural boundaries and detecting dependency issues.

## Config Files

| File | Purpose |
|------|---------|
| `.importlinter` | Import rules: layers, isolation, forbidden imports |
| `tach.toml` | Module boundaries and layer definitions |

## Tools

| Tool | Purpose | Config | Script |
|------|---------|--------|--------|
| **import-linter** | Enforce import rules (layers, isolation, forbidden) | `.importlinter` | `tools/lint_imports.sh` / `.bat` |
| **tach** | Module boundaries & layer enforcement | `tach.toml` | `tools/tach_check.sh` / `.bat` |
| **pycycle** | Detect circular imports | - | `tools/pycycle_check.sh` / `.bat` |
| **pydeps** | Visualize dependencies | - | `tools/pydeps_graph.sh` / `.bat` |

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

## CI

All checks run automatically on pull requests (see `.github/workflows/ci.yml`).

## Current Contracts (import-linter)

**Architecture (6)**: Layered architecture, domain independence, formatter independence, external services independence, git local isolation, jenkins isolation

**Third-party (11)**: github, git, jenkins, claude_code_sdk, pyperclip, mcp_code_checker, requests, structlog, pythonjsonlogger, black, isort

**Tests (2)**: No test imports in source, test module independence

> Each rule includes comments explaining its rationale. See `.importlinter` and `tach.toml` for details.

## When to Add New Rules

**Add a third-party isolation rule when:**
- Adding a new external dependency
- The library should only be used by a specific module (wrapper pattern)

**Add an architecture rule when:**
- Creating a new top-level module that needs layer assignment
- Two modules should remain independent (no cross-imports)
- A module should never import from another (forbidden)

**Update existing rules when:**
- Moving or renaming modules
- Intentionally allowing a previously forbidden import (add to `ignore_imports`)

## Generated Files

- `dependency_graph.html` - Interactive dependency visualization (committed)
- `pydeps_graph.svg` / `.dot` - Pydeps visualization (generate with `tools/pydeps_graph.sh`)
