# Decisions — Issue #264

## 1. `_prepare_restart_branch` signature change

**Decision:** Pass a single `repo_full_name: str` parameter (not two separate `repo_owner`/`repo_name` params). Split inside the function.

**Rationale:** More Pythonic, keeps the signature minimal, and matches the existing pattern throughout the codebase.

## 2. Closed-PR fallback ordering

**Decision:** Sort closed PRs by most recent first (highest PR number descending) before iterating.

**Rationale:** The most recently closed PR is more likely to be the relevant branch. PR `number` is already in the timeline data, so no extra API call needed.

## 3. Pattern search API efficiency

**Decision:** Two-pass approach:
1. First try `get_git_matching_refs(f"heads/{issue_number}")` — cheap, catches `123-foo` style branches
2. If no match, fall back to `get_git_matching_refs("heads/")` with 500 cap — catches nested patterns like `feature/123-foo`

**Rationale:** Optimizes the common case (direct-prefix branches) without sacrificing coverage of nested naming conventions.

## 4. Performance impact on `build_eligible_issues_with_branch_check`

**Decision:** Accept the heavier API cost. No fast-path or special handling needed.

**Rationale:** The function runs infrequently and correctness matters more than speed. The extra fallback steps only fire when the fast path (linkedBranches) fails.

## 5. `_handle_intervention_mode` repo extraction

**Decision:** Use `RepoIdentifier.from_repo_url(repo_url)` to extract owner/name.

**Rationale:** Standard pattern in the codebase. Avoids coupling to private `BaseGitHubManager` internals.
