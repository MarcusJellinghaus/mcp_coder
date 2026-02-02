# Decisions for Issue #365

Decisions made during plan review discussion.

## Decision 1: `update_issue_labels_in_cache` Export

**Question:** After renaming `_update_issue_labels_in_cache` to `update_issue_labels_in_cache`, should this function remain exported from the coordinator package's `__init__.py`?

**Decision:** **Remove from `__init__.py`**

The function will be imported directly in `commands.py` from `issue_cache.py`. No need to re-export it at the coordinator package level.

## Decision 2: `CacheData` Export

**Question:** Is `CacheData` used by code outside the coordinator package, or is it only used internally/for testing?

**Investigation:** Searched the codebase and found:
- `CacheData` is defined in `issue_cache.py`
- It's re-exported in `coordinator/__init__.py` but this re-export is unused
- All actual imports come directly from `issue_cache.py` (e.g., in `tests/utils/github_operations/conftest.py`)
- Within `coordinator/core.py`, it's imported directly from `issue_cache.py`, not via the coordinator package

**Decision:** **Remove from `__init__.py`**

The re-export is dead code - nobody imports `CacheData` from the coordinator package.

## Decision 3: `_update_issue_labels_in_cache` Import in `core.py`

**Question:** The function `_update_issue_labels_in_cache` is imported in `core.py` but never used there. It's only imported for re-export via `__init__.py`. Should we update this import (to the renamed version) or remove it entirely?

**Decision:** **Remove from `core.py` entirely**

Since the function is never used in `core.py`, remove the import completely. `commands.py` will import `update_issue_labels_in_cache` directly from `issue_cache.py`.
