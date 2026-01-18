# Decisions Log

Decisions made during plan review discussion.

---

## Decision 1: BASE_BRANCH File Support

**Question**: Should we include `pr_info/BASE_BRANCH` file as a fallback for parent branch detection?

**Decision**: **No, do not include it**

**Rationale**: Keep implementation simple. GitHub PR base branch detection + default branch fallback is sufficient. If a PR exists, we use its base branch; otherwise, we fall back to main/master. The BASE_BRANCH file would add complexity for a rare edge case.

---

## Decision 2: Dirty Working Directory Handling

**Question**: Should `rebase_onto_branch()` explicitly check for clean working directory, or rely on prerequisite check?

**Decision**: **Rely on prerequisite check**

**Rationale**: `check_git_clean()` already runs before rebase step in the workflow. Keep `rebase_onto_branch()` simple.

---

## Decision 3: Force Push After Rebase

**Question**: How should we handle pushing after rebase (when local history diverges from remote)?

**Decision**: **Use `--force-with-lease`**

**Rationale**: Safer than `--force` - fails if remote has unexpected changes. Feature branch context makes force push acceptable.

---

## Decision 4: Force Push API Design

**Question**: Should the API use a boolean parameter or flexible string argument?

**Decision**: **Boolean parameter `force_with_lease: bool = False`**

**Rationale**: Simple, type-safe, self-documenting. Can extend with additional parameters later if needed (YAGNI).

---

## Decision 5: Test Coverage Gaps

**Question**: Should we add tests for edge cases (missing GitHub token fallthrough, empty BASE_BRANCH file)?

**Decision**: **Skip - existing coverage sufficient**

**Rationale**: Minor edge cases, existing test coverage is adequate.

---

## Decision 6: Plan Structure

**Question**: Should force push changes be a new Step 3, or added to Step 1?

**Decision**: **Add to Step 1**

**Rationale**: Keep 2 steps total. Step 1 covers all `git_operations` changes (both `branches.py` and `remotes.py`).
