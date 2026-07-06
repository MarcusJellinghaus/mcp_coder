# Safe Refactoring Guide

Guidelines for refactoring code safely, whether splitting large files or restructuring architecture.

**File-size threshold: 750 lines** — the canonical hard limit, enforced in CI (`.github/workflows/ci.yml`). The MCP `check_file_size` tool historically defaults to 600; treat that as an informal early-warning and 750 as the hard limit.

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

### Step 2: Move Source Code (Using MCP Refactoring Tools)

Use the MCP refactoring tools — they move code and update all imports automatically:

1. `mcp__mcp-tools-py__list_symbols(file=...)` — inventory the source file
2. `mcp__mcp-tools-py__move_symbol(source_file=..., symbol_name=..., dest_file=..., dry_run=true)` — preview
3. `mcp__mcp-tools-py__move_symbol(source_file=..., symbol_name=..., dest_file=...)` — execute
4. Repeat for each symbol/group
5. Update `__init__.py` re-exports if needed
6. Update `.importlinter` layering contracts if the split introduces sub-layers (see [Import Linter](#import-linter) below)

### Step 3: Move Tests

Tests should mirror source structure:

```
src/mcp_coder/utils/string_helpers.py
tests/utils/test_string_helpers.py
```

Split **source and its tests together in one PR**, per module. **Rename misnamed tests to parallel names** while you split (`core.py` tested by `test_main.py`; `agent.py` by `test_langchain_agent_streaming.py`). When one module's tests dwarf its source, see [Splitting Large Files](#splitting-large-files).

### Step 4: Verify

After all moves, verify the refactoring:

#### Compact Diff

```bash
mcp-coder git-tool compact-diff
```

Suppresses moved-code blocks from the diff output. After a pure refactoring, the remaining diff should contain **only import changes and new/deleted file headers**. If you see logic changes in the compact diff, something was modified during the move.

#### File Size Check

**For humans / CI:**

```bash
mcp-coder check file-size --max-lines 750
```

**For LLM sessions (MCP tools):**

```
mcp__mcp-workspace__check_file_size
```

Verifies all tracked Python files are under the line threshold. If split files were previously in `.large-files-allowlist`, remove those entries — a split isn't complete until the file is under 750 **and** off the allowlist. Stale entries are reported automatically.

#### Import Linter

When splitting a module into sub-modules, the new files may have internal dependencies (e.g. `branch_queries` imports from `repository_status`). If the import linter uses a `layers` contract with `|` (pipe) separators, siblings can't import each other.

**Fix:** Use sub-layers — put the dependency on a lower layer than its consumers:
```ini
# Before (single module):
    mcp_coder.utils.git_operations.readers

# After (split into sub-layers):
    mcp_coder.utils.git_operations.branch_queries | mcp_coder.utils.git_operations.parent_branch_detection
    mcp_coder.utils.git_operations.repository_status
```

#### Standard Checks

**For humans / CI:**

```bash
# Import structure
./tools/lint_imports.sh
./tools/tach_check.sh
```

**For Claude Code (MCP tools):**

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_lint_imports_check
mcp__mcp-tools-py__run_vulture_check
mcp__mcp-tools-py__run_pytest_check
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_mypy_check
```

> `tach_check.sh` and `pycycle_check.sh` have no MCP equivalents — run them via Bash when needed.
> Use `mcp__mcp-tools-py__get_library_source` to inspect third-party library APIs when planning refactors.

## Common Patterns

### Architectural Restructuring

1. Update `.importlinter` and `tach.toml` with new module boundaries
2. Move code to match new structure
3. Fix any import violations
4. Update architecture documentation

## Splitting Large Files

Technique for getting oversized files under the 750-line limit, plus the issue-lifecycle rules for running the effort ([Workflow](#workflow-issue-lifecycle), below).

**Tracking:** live inventory of oversized files — issue #353. Find command / CLI — #75. First worked example — #257.

### Find the files (mind the allowlist)

`mcp__mcp-workspace__check_file_size` and the default `mcp-coder check file-size` **hide files listed in `.large-files-allowlist`** — so the biggest offenders (already allowlisted) are invisible in the normal output. To see the true full picture, bypass the allowlist by pointing it at a nonexistent path:

```bash
mcp-coder check file-size --max-lines 750 --allowlist-file .no-such-allowlist
```

Build your inventory from this full list, not the filtered one — otherwise the largest files get systematically overlooked (they were allowlisted precisely because they're huge).

### Split a large file

1. Identify logical groupings (by responsibility, by domain)
2. Create new files for each group
3. Move functions one group at a time
4. Delete the original file — update all consumers to use new locations directly

### When tests are much larger than the source

The `foo.py ↔ test_foo.py` rule mirrors **structure, not file count** — one source module maps to one test *namespace* that may hold several files.

- **Default: split the tests** by concern into that namespace, **mirroring the source**: a *package* → a test directory (`tests/workflows/create_plan/test_*.py`); a *single module* → prefixed sibling files (`test_core.py` + `test_core_safety_net.py`). Don't restructure source just to satisfy a filename.
- **Exception: refactor the source** — only if decomposing it is a design win you'd want *even without the line limit* (a monolith with inlined responsibilities, not a thin coordinator). Then it's a `refactor`, not a mechanical split — see [Workflow](#workflow-issue-lifecycle).

### Test-only splits (orphan tests)

Some test files exceed the limit while their source file is fine. Split these on their own — no source move; break the test file into parallel-named pieces by concern and delete the original.

### Workflow (issue lifecycle)

How to run splitting issues (distinct from the code technique above):

- **Definition of done / closure gating:** close a split issue only once the file is under **750** lines **and** its `.large-files-allowlist` entry is removed. Closing while still allowlisted is a silent regression — e.g. #310 was closed but stayed 949 lines & allowlisted, now refiled as #1025.
- **No recycling:** if a split file grows back over the limit, open a **new** issue — do not reopen the closed one.
- **Source-refactor exception:** when [tests dwarf the source](#when-tests-are-much-larger-than-the-source) and decomposing it is warranted, it's a `refactor`, not a mechanical split. The LLM **proposes** it and a **human confirms** before the split is paused; then re-scope the issue up front, or open a separate issue and mark the split `blocked` if found mid-split.

## Checklist

Before merging a refactoring PR:

- [ ] No function/class logic was changed (only moved) — verify with `mcp-coder git-tool compact-diff`
- [ ] All imports updated correctly (automatic when using `move_symbol`)
- [ ] Tests moved to mirror source structure
- [ ] `lint-imports` passes
- [ ] `tach check` passes
- [ ] All unit tests pass
- [ ] File size check passes (`mcp-coder check file-size --max-lines 750` or `mcp__mcp-workspace__check_file_size`)
- [ ] `.large-files-allowlist` updated (remove entries for split files)
- [ ] `.importlinter` updated if modules were split (sub-layers)
- [ ] PR diff is under 25,000 tokens

## Related

- [Refactoring Principles](../../.claude/knowledge_base/refactoring_principles.md) — quick-reference rules and tool tables (loaded by slash commands)
- [Architecture Documentation](../architecture/architecture.md)
- [Dependency Management](../architecture/dependencies/readme.md)
