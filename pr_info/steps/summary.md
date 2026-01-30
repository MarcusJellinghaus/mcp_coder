# Feature: Base Branch Support for Issues - Implementation Summary

## Overview

Add support for specifying a `base_branch` in GitHub issues, allowing work to start from branches other than the repository default. This enables hotfixes, release branches, and features building on existing work.

**Backward Compatibility**: Existing issues without `### Base Branch` section continue using repository default.

---

## Architectural / Design Changes

### Data Flow Changes

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  GitHub Issue   │────►│  IssueManager    │────►│  create_plan.py     │
│  (body text)    │     │  _parse_base_    │     │  manage_branch()    │
│                 │     │  branch()        │     │                     │
│ ### Base Branch │     │                  │     │  passes base_branch │
│ feature/v2      │     │  IssueData with  │     │  to branch creation │
└─────────────────┘     │  base_branch     │     └─────────────────────┘
                        └──────────────────┘               │
                                                           ▼
                                              ┌─────────────────────────┐
                                              │ IssueBranchManager      │
                                              │ create_remote_branch_   │
                                              │ for_issue(base_branch=) │
                                              └─────────────────────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Parse in `issue_manager.py` | Single responsibility - parsing is issue-related |
| No separate validation function | `create_remote_branch_for_issue()` already validates via `repo.get_branch()` |
| Error on multi-line content | Malformed input should block branch creation early |
| `NotRequired[Optional[str]]` | Backward compatible - field is optional in TypedDict |

### Changes by Component

| Component | Change Type | Description |
|-----------|-------------|-------------|
| `IssueData` TypedDict | **Extension** | Add `base_branch: NotRequired[Optional[str]]` |
| `issue_manager.py` | **New function** | Add `_parse_base_branch()` |
| `issue_manager.py` | **Modification** | Populate `base_branch` in `get_issue()`, `list_issues()` |
| `create_plan.py` | **Modification** | Pass `base_branch` to branch creation |
| `pr_manager.py` | **Bug fix** | Change hardcoded `"main"` to dynamic default |
| Slash commands | **Documentation** | Add base branch guidance |

---

## Files to Create or Modify

### Source Files (Modify)

| File | Changes |
|------|---------|
| `src/mcp_coder/utils/github_operations/issue_manager.py` | Add `_parse_base_branch()`, extend `IssueData`, populate in `get_issue()`/`list_issues()` |
| `src/mcp_coder/workflows/create_plan.py` | Update `manage_branch()` to accept and pass `base_branch` |
| `src/mcp_coder/utils/github_operations/pr_manager.py` | Fix `create_pull_request()` default parameter |

### Test Files (Modify)

| File | Changes |
|------|---------|
| `tests/utils/github_operations/test_issue_manager.py` | Add tests for `_parse_base_branch()` |
| `tests/workflows/create_plan/test_branch_management.py` | Add tests for base_branch parameter passing |

### Documentation Files (Modify)

| File | Changes |
|------|---------|
| `.claude/commands/issue_analyse.md` | Add base branch display guidance |
| `.claude/commands/issue_create.md` | Add base branch field documentation |
| `.claude/commands/issue_update.md` | Add base branch editing guidance |
| `docs/repository-setup.md` | Document the base branch feature |

---

## Implementation Steps Overview

| Step | Focus | Files |
|------|-------|-------|
| **Step 1** | Core parsing: `_parse_base_branch()` + tests | `issue_manager.py`, `test_issue_manager.py` |
| **Step 2** | Extend `IssueData` and populate in `get_issue()`/`list_issues()` | `issue_manager.py`, `test_issue_manager.py` |
| **Step 3** | Pass `base_branch` through `create_plan.py` workflow | `create_plan.py`, `test_branch_management.py` |
| **Step 4** | Fix hardcoded "main" in `pr_manager.py` | `pr_manager.py`, `test_pr_manager.py` |
| **Step 5** | Update slash commands and documentation | `.claude/commands/*.md`, `docs/repository-setup.md` |

---

## Issue Body Format (Reference)

```markdown
### Base Branch

feature/existing-work

### Description

The actual issue content...
```

### Parsing Rules

- **Case-insensitive** match for `Base Branch` header (any heading level: `#`, `##`, `###`)
- Capture content until next `#` header
- Strip whitespace; empty/whitespace-only → `None` (use repo default)
- **Error** if content has multiple lines (malformed, blocks branch creation)

---

## Test Cases Summary

```python
# Valid base branches
("### Base Branch\n\nfeature/v2\n\n### Description", "feature/v2")
("# base branch\n\nmain\n\n# Description", "main")  # Case insensitive
("## BASE BRANCH\n\nrelease/2.0\n\n## Description", "release/2.0")  # Uppercase

# No base branch (returns None)
("### Description\n\nNo base branch section", None)
("### Base Branch\n\n\n\n### Description", None)  # Empty
("### Base Branch\n\n   \n\n### Description", None)  # Whitespace-only

# Errors (raises ValueError)
("### Base Branch\n\nline1\nline2\n\n### Description", ValueError)  # Multi-line
```
