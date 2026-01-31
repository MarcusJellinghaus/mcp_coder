# Safe Refactoring Guide

Guidelines for refactoring code safely, whether splitting large files or restructuring architecture.

## Why This Matters

Large files (>750 lines) and poor code organization:

- Consume excessive LLM context
- Make navigation difficult
- Increase merge conflict risk
- Obscure architectural boundaries

## Core Principles

### 1. Move, Don't Change

**Critical rule**: Functions and classes should be moved, not modified.

```python
# GOOD: Function moved as-is
# old: src/utils/helpers.py
# new: src/utils/string_helpers.py

# BAD: Function modified during move
# Changing logic while relocating - do this in a separate PR
```

### 2. Only Adjust Imports

The only code changes should be:

- Import statements in the moved file
- Import statements in files that use the moved code
- Re-exports in `__init__.py` files (if maintaining API compatibility)

### 3. Clean Deletion, No Legacy Artifacts

When moving code to a new location:

- **Delete the old files entirely** - Do not leave empty modules or stubs
- **No deprecation warnings** - Update all consumers to use the new location directly
- **No re-exports for backward compatibility** - This creates hidden dependencies and technical debt
- **Update all imports immediately** - Every file that imported from the old location must be updated

Clean code is preferred over gradual migration. If external packages depend on the old location, coordinate the change or document it as a breaking change.

### 4. Small Steps

LLMs struggle with large moves. Break refactoring into:

- **One module per PR** when possible
- **Keep PR diffs under 25,000 tokens**
- **Move related functions together** (e.g., all string utilities)

## Process

### Step 1: Plan the Target Structure

Before moving anything:

1. Identify the "ideal" location for each component
2. Check that test files mirror source structure
3. Verify the new structure aligns with import linter / tach rules

### Step 2: Move Source Code

1. Create the new file(s)
2. Move functions/classes (copy-paste, no modifications)
3. Update imports in the new file
4. Update imports in consuming files
5. Update `__init__.py` re-exports if needed

### Step 3: Move Tests

Tests should mirror source structure:

```
src/mcp_coder/utils/string_helpers.py
tests/utils/test_string_helpers.py
```

### Step 4: Verify

Run all checks after each move:

```bash
# Import structure
./tools/lint_imports.sh
./tools/tach_check.sh

# Functionality (Claude Code MCP tools)
mcp__code-checker__run_pytest_check
mcp__code-checker__run_pylint_check
mcp__code-checker__run_mypy_check
```

## Common Patterns

### Splitting a Large File

1. Identify logical groupings (by responsibility, by domain)
2. Create new files for each group
3. Move functions one group at a time
4. Keep the original file as a facade (re-exports) if external code depends on it

### Architectural Restructuring

1. Update `.importlinter` and `tach.toml` with new module boundaries
2. Move code to match new structure
3. Fix any import violations
4. Update architecture documentation

## Checklist

Before merging a refactoring PR:

- [ ] No function/class logic was changed (only moved)
- [ ] All imports updated correctly
- [ ] Tests moved to mirror source structure
- [ ] `lint-imports` passes
- [ ] `tach check` passes
- [ ] All unit tests pass
- [ ] PR diff is under 25,000 tokens

## Related

- [Architecture Documentation](../architecture/architecture.md)
- [Dependency Management](../architecture/dependencies/readme.md)
