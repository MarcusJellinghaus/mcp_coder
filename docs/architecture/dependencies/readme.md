# Dependency Management

Why the architecture rules are enforced, and which tools enforce them: see [Architecture Enforcement](../enforcement.md). This page keeps the details that do not fit there.

## Why Both import-linter and tach?

| Feature | import-linter | tach |
|---------|---------------|------|
| Layer enforcement | ✅ | ✅ |
| Third-party isolation | ✅ `forbidden` contracts | ❌ |
| Submodule boundaries | ✅ `\|` siblings in the layers contract, `forbidden` contracts | ❌ (struggles with `__init__.py`) |
| Circular dependency detection | ⚠️ targeted `forbidden` contracts only (e.g. `mlflow_logger_no_cycles`) | ✅ |
| Explicit `depends_on` | ❌ | ✅ |

**Summary**: Use both - tach for high-level layers, import-linter for fine-grained rules.

## Best Practice: Submodule Imports

**Rule:** Submodules should never import from their parent `__init__.py`. Import from siblings directly.

```python
# BAD - triggers loading of ALL sibling submodules
from mcp_coder.utils import get_default_branch_name

# GOOD - only loads the specific sibling module
from mcp_coder.utils.git_operations import get_default_branch_name
```

**Why:** When `utils/__init__.py` re-exports symbols from all submodules, importing from the parent loads everything - creating unintended transitive dependencies between siblings.

**The facade pattern:** Keep `__init__.py` as a convenient facade for *external* consumers (workflows, CLI), but *internal* submodules must import siblings directly.

## Refactoring

When restructuring code or splitting large files, see the [Safe Refactoring Guide](../../processes-prompts/refactoring-guide.md) for best practices on moving code without breaking imports.

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

## Vulture Whitelist

**Whitelist**: `vulture_whitelist.py` contains items that appear unused but are intentionally kept:
- API completeness methods (GitHub operations)
- Enum values for API constants
- Base class attributes for subclasses
- TypedDict fields, pytest fixtures, argparse patterns (false positives)

**Note**: The whitelist is intentionally liberal. Some items may be candidates for removal but were whitelisted to avoid blocking implementation. Review the whitelist periodically - items may become used or truly dead over time.

## Generated Files

- `dependency_graph.html` - Interactive dependency visualization (committed)
- `pydeps_graph.dot` - Pydeps graph source (committed)
- `pydeps_graph.svg` - Pydeps visualization (generate with `tools/pydeps_graph.sh`)
