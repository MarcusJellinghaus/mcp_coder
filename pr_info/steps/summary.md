# Issue #264: Coordinator — Detect Unlinked Branches by Issue Number Pattern

## Summary

The coordinator's `branch_strategy: from_issue` resolves branches via GitHub's `linkedBranches` GraphQL API and an open-PR timeline fallback. If a branch exists on the remote matching the issue number (e.g., `feature/252-foo`) but isn't formally linked, the coordinator skips the issue. Additionally, the VSCodeClaude code path (`get_linked_branch_for_issue()`) only checks `linkedBranches` with no PR or pattern fallback, and uses `ValueError` exceptions for expected control flow.

This change enhances `get_branch_with_pr_fallback()` with two new resolution steps (closed-PR fallback, branch pattern search), unifies all callers onto this single resolution method, and replaces `ValueError` signaling with `None` returns.

## Architectural / Design Changes

### Before (current state)
```
Coordinator path:
  get_branch_with_pr_fallback()
    1. linkedBranches → return first (even if multiple)
    2. Open PRs from timeline → return if exactly one

VSCodeClaude path:
  get_linked_branch_for_issue()
    1. get_linked_branches() → return if one, raise ValueError if multiple
    (NO PR fallback, NO pattern search)
```

Two separate resolution paths. `ValueError` used for ambiguous branches. Closed PRs and unlinked branches are invisible.

### After (target state)
```
Single unified path — all callers use get_branch_with_pr_fallback():
  1. linkedBranches → return None if multiple (ambiguous)
  2. Open PRs from timeline → existing behavior
  3. Closed (not merged) PRs → NEW: verify branch exists, 25-check cap
  4. Branch pattern search → NEW: regex (^|/)N[-_], 500-branch cap
```

- `get_linked_branch_for_issue()` removed entirely
- All callers call `branch_manager.get_branch_with_pr_fallback()` directly
- No more `ValueError` — `None` means "can't resolve" in all cases
- `_extract_open_prs()` generalized to `_extract_prs_by_states(items, states)`

### Key design decisions preserved from issue

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Pattern regex | `(^|/)N[-_]` | Covers common naming without being too broad |
| Closed PR cap | 25 `get_branch()` calls | Caps expensive API, not cheap filtering |
| Pattern search cap | 500 branches | Sufficient for matching; avoids runaway API |
| Pattern match log | INFO level | Notable event worth surfacing |
| Multiple linked branches | Return `None` | Consistent with how multiple PRs are handled |
| Closed PR ordering | Most recent first (by PR number desc) | Most recently closed PR is most likely relevant |
| Pattern search strategy | Two-pass: prefix match first, full scan fallback | Optimizes common case without sacrificing coverage |
| `_prepare_restart_branch` param | Single `repo_full_name: str` | Matches existing codebase pattern, split inside function |
| Intervention mode repo extraction | `RepoIdentifier.from_repo_url()` | Standard codebase pattern, avoids private API coupling |

## Files Modified

### Core logic
| File | Change |
|------|--------|
| `src/mcp_coder/utils/github_operations/issues/branch_manager.py` | Generalize `_extract_open_prs` → `_extract_prs_by_states`, add `_search_branches_by_pattern`, extend `get_branch_with_pr_fallback` with closed-PR and pattern-search steps, return `None` for multiple linked branches |

### Caller updates (remove wrapper, remove ValueError handling)
| File | Change |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | Delete `get_linked_branch_for_issue()`, remove `try/except ValueError` in `build_eligible_issues_with_branch_check()` |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | Replace `get_linked_branch_for_issue` with `branch_manager.get_branch_with_pr_fallback()`, remove `try/except ValueError` |
| `src/mcp_coder/workflows/vscodeclaude/session_restart.py` | Replace `get_linked_branch_for_issue` with `branch_manager.get_branch_with_pr_fallback()`, remove `try/except ValueError` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Replace `get_linked_branch_for_issue` with `branch_manager.get_branch_with_pr_fallback()`, add intervention-mode warning for `None` |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | Remove `get_linked_branch_for_issue` from exports |

### Tests
| File | Change |
|------|--------|
| `tests/utils/github_operations/issues/test_branch_resolution.py` | Add tests for: `_extract_prs_by_states`, closed-PR fallback, pattern search, multiple-linked-branches |
| `tests/workflows/vscodeclaude/test_issues.py` | Remove `ValueError` tests, update `build_eligible_issues_with_branch_check` tests |
| `tests/workflows/vscodeclaude/test_orchestrator_launch.py` | Update mocks: `get_branch_with_pr_fallback` instead of `get_linked_branch_for_issue` |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | Update mocks: `get_branch_with_pr_fallback` instead of `get_linked_branch_for_issue` |

## Implementation Steps

| Step | Description | Approach |
|------|-------------|----------|
| 1 | Enhance `branch_manager.py` — core resolution logic | TDD: tests first for new methods, then implement |
| 2 | Remove wrapper, update all callers | TDD: update caller tests first, then modify callers |
| 3 | Update existing test suites | Fix remaining mocks and assertions across test files |

## Risk Assessment

- **Low risk**: All new resolution steps are additive fallbacks — existing linkedBranches and open-PR paths are unchanged in logic
- **Medium risk**: Removing `ValueError` changes caller contracts — but all callers already handle `None`, so the `except ValueError` blocks were just routing to the same `None`/skip path
- **Latent bug fixed**: `_handle_intervention_mode()` never caught `ValueError` — would crash on multi-branch issues. After this change it naturally gets `None` and logs a warning
