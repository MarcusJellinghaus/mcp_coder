# Architecture Decisions

## Decision 1: Move `branch_status.py` to `workflow_utils/`

**Context**: `branch_status.py` is in the infrastructure layer (`utils/`) but imports from the application layer (`workflow_utils.task_tracker`).

**Options Considered**:
1. **Move `branch_status.py` to `workflow_utils/`** - Recognizes it as application-level code
2. **Dependency Inversion** - Pass task status as parameter
3. **Extract task parsing to infrastructure** - Create low-level parser in `utils/`

**Decision**: Option 1 - Move to `workflow_utils/`

**Rationale**:
- Branch status is workflow-specific state reporting, not generic infrastructure
- Minimal changes required (just move file and update imports)
- Conceptually correct placement
- No API changes needed

## Decision 2: Move `needs_rebase` to `workflows.py`

**Context**: `branches.py` imports `fetch_remote` from `remotes.py`, violating the same-layer independence rule within `git_operations`.

**Options Considered**:
1. **Move `needs_rebase` to `workflows.py`** - It orchestrates multiple operations
2. **Move `fetch_remote` to `readers.py`** - But fetch modifies state, not a reader
3. **Add exception to import-linter** - Masks the architectural issue

**Decision**: Option 1 - Move `needs_rebase` to `workflows.py`

**Rationale**:
- `needs_rebase` orchestrates fetch + branch comparison (workflow behavior)
- `workflows.py` is the orchestration layer (Layer 0)
- Keeps `branches.py` focused on local branch operations

## Decision 3: Whitelist `__getattr__` for Vulture

**Context**: Vulture reports `__getattr__` in `workflow_utils/__init__.py` as unused at 60% confidence.

**Decision**: Add to vulture whitelist

**Rationale**:
- `__getattr__` is a Python magic method for lazy imports
- It's called implicitly by Python, not directly in code
- This is a false positive (vulture cannot detect implicit usage)

## Decision 4: Investigate Force-With-Lease Test

**Context**: Test `test_git_push_force_with_lease_fails_on_unexpected_remote` expects failure but gets success.

**Decision**: Investigate git behavior differences between local and CI environments

**Rationale**:
- May be a timing issue or git version difference
- Need to understand why force-with-lease succeeds when it should fail
