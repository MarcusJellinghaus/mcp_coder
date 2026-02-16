# Implementation Plan: Branch Resolution with PR Fallback (Issue #219)

## Quick Reference

**Issue:** #219 - No linked branch found for issues with draft PRs  
**Approach:** KISS principle - extend existing `IssueBranchManager` with fallback method  
**Strategy:** Test-Driven Development (TDD) - tests first, implementation second  

---

## Implementation Overview

### Architecture Decision: Keep It Simple
Instead of creating a new module with complex result types (enum, TypedDict), we:
- ✅ Add **one method** to existing `IssueBranchManager`
- ✅ Return simple `Optional[str]` (branch name or None)
- ✅ Reuse existing error handling patterns
- ✅ Minimal code changes (~120 lines added, ~15 modified)

### Two-Step Fallback Strategy
```
Step 1: Query linkedBranches (fast, primary)
        ↓
Step 2: Query PR timeline (fallback if step 1 empty)
        ↓
Result: Branch name or None
```

---

## Files Created/Modified

### Modified Files (2)
1. **`src/mcp_coder/utils/github_operations/issues/branch_manager.py`**
   - Add `get_branch_with_pr_fallback()` method (~100 lines)
   - Uses GraphQL timeline query for PR fallback
   - Returns `Optional[str]`

2. **`src/mcp_coder/cli/commands/coordinator/core.py`**
   - Update `dispatch_workflow()` function
   - Add import for `parse_github_url`
   - Replace branch resolution call (~15 lines changed)

### Created Files (1)
3. **`tests/utils/github_operations/issues/test_branch_resolution.py`** (NEW)
   - 8 comprehensive test scenarios (some parametrized)
   - Covers primary path, fallback, edge cases
   - ~280 lines using hybrid approach with parametrization

---

## Implementation Steps

### Step 1: Test Suite Foundation (TDD) 📝
**Goal:** Write failing tests first

**Actions:**
- Create `test_branch_resolution.py`
- Write 8 test scenarios
- All tests fail (method doesn't exist yet)

**Duration:** ~30 minutes  
**Verification:** `pytest test_branch_resolution.py` → 8 failures expected

**LLM Prompt:** See `pr_info/steps/step_1.md`

---

### Step 2: Core Method Implementation ⚙️
**Goal:** Make all tests pass

**Actions:**
- Add `get_branch_with_pr_fallback()` to `branch_manager.py`
- Implement two-step fallback logic
- GraphQL timeline query for PRs

**Duration:** ~45 minutes  
**Verification:** `pytest test_branch_resolution.py` → 8 passes expected

**LLM Prompt:** See `pr_info/steps/step_2.md`

---

### Step 3: Coordinator Integration 🔗
**Goal:** Use new method in production code

**Actions:**
- Update `dispatch_workflow()` in coordinator
- Add URL parsing for repo owner/name
- Replace old `get_linked_branches()` call
- Enhanced error logging

**Duration:** ~20 minutes  
**Verification:** Existing coordinator tests still pass

**LLM Prompt:** See `pr_info/steps/step_3.md`

---

### Step 4: Quality Verification ✅
**Goal:** Ensure all quality checks pass

**Actions:**
- Run pytest (new + existing tests)
- Run mypy (type checking)
- Run pylint (code quality)
- Fix any issues found

**Duration:** ~30 minutes  
**Verification:** All checks pass, score ≥9.0/10

**LLM Prompt:** See `pr_info/steps/step_4.md`

---

## Total Estimated Time
**2-2.5 hours** for complete implementation and verification

---

## Step-by-Step Execution Guide

### Execute Steps in Order

```bash
# Step 1: Create Tests (TDD)
# Read: pr_info/steps/step_1.md
# Create: tests/utils/github_operations/issues/test_branch_resolution.py
# Verify: pytest test_branch_resolution.py → 8 failures

# Step 2: Implement Method
# Read: pr_info/steps/step_2.md
# Modify: src/mcp_coder/utils/github_operations/issues/branch_manager.py
# Verify: pytest test_branch_resolution.py → 8 passes

# Step 3: Integrate with Coordinator
# Read: pr_info/steps/step_3.md
# Modify: src/mcp_coder/cli/commands/coordinator/core.py
# Verify: pytest tests/cli/commands/coordinator/ → all pass

# Step 4: Quality Checks
# Read: pr_info/steps/step_4.md
# Run: mcp__code-checker__run_all_checks()
# Verify: All checks pass
```

---

## Key Design Principles Applied

### 1. KISS (Keep It Simple, Stupid)
- ❌ Rejected: Separate module with complex result types
- ✅ Accepted: Single method in existing class
- **Benefit:** Less code, easier maintenance

### 2. TDD (Test-Driven Development)
- ✅ Write tests first (Step 1)
- ✅ Implement to make tests pass (Step 2)
- ✅ Refactor if needed (Step 4)
- **Benefit:** Confidence in correctness

### 3. Single Responsibility
- Each step has one clear goal
- Each method does one thing well
- **Benefit:** Clear code, easy to understand

### 4. Fail Fast, Fail Loud
- Invalid inputs → return None immediately
- Multiple PRs → return None with warning
- API errors → handled by decorator
- **Benefit:** Clear error messages

---

## Acceptance Criteria Mapping

| Requirement | Implementation | Verification |
|-------------|----------------|--------------|
| Query linkedBranches first | Primary path in method | Step 1: test_linked_branch_found |
| Query PR timeline fallback | Fallback path in method | Step 1: test_single_draft_pr |
| Handle multiple PRs | Return None, log warning | Step 1: test_multiple_prs |
| Coordinator uses new method | Updated dispatch_workflow | Step 3: integration |
| Comprehensive error logging | Enhanced log messages | Step 3: code review |
| Non-blocking errors | Return early, continue loop | Step 3: code review |
| Unit tests pass | All 8 scenarios | Step 4: pytest |
| Quality checks pass | pylint, mypy, pytest | Step 4: all checks |
| No closed issue changes | No changes needed | N/A (already filtered) |

---

## Technical Architecture

### Method Signature
```python
@log_function_call
@_handle_github_errors(default_return=None)
def get_branch_with_pr_fallback(
    self,
    issue_number: int,
    repo_owner: str,
    repo_name: str,
) -> Optional[str]:
    """Get branch for issue via linkedBranches or draft/open PR fallback."""
```

### GraphQL Timeline Query
```graphql
query($owner: String!, $repo: String!, $issueNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $issueNumber) {
      timelineItems(itemTypes: [CROSS_REFERENCED_EVENT], first: 100) {
        nodes {
          __typename
          ... on CrossReferencedEvent {
            source {
              ... on PullRequest {
                number
                state
                isDraft
                headRefName
              }
            }
          }
        }
      }
    }
  }
}
```

### Resolution Logic Flow
```python
# 1. Validate input
if invalid: return None

# 2. Try linkedBranches (fast path)
if branches: return branches[0]

# 3. Query PR timeline (fallback)
prs = query_timeline()

# 4. Filter open PRs (includes drafts)
filtered = [pr for pr in prs if pr.state == "OPEN"]

# 5. Return result
if len(filtered) == 1: return filtered[0].headRefName
else: return None
```

---

## Dependencies

### Internal (Already Exist)
- `IssueBranchManager.get_linked_branches()` - reused
- `@_handle_github_errors` decorator - error handling
- `parse_github_url()` - URL parsing
- PyGithub GraphQL API - timeline queries

### External
- GitHub GraphQL API (timeline queries)
- PyGithub library

### No New Dependencies Required ✅

---

## Risk Assessment

### Low Risk ✅
- **Why:** Changes are additive, not destructive
- **Existing functionality:** Unchanged
- **New method:** Only used in one place (coordinator)
- **Rollback:** Simple (revert coordinator changes)

### Testing Coverage
- **8 unit tests** for new method
- **Existing tests** verify no regressions
- **Manual scenarios** documented in Step 3

---

## Performance Considerations

### Primary Path (linkedBranches)
- **Speed:** <100ms (existing GraphQL query)
- **Frequency:** Most common case
- **Impact:** None (existing code path)

### Fallback Path (PR Timeline)
- **Speed:** ~500ms (additional GraphQL query)
- **Frequency:** Only when linkedBranches empty
- **Impact:** Minimal (rare case, acceptable latency)

### Optimization Opportunities (Future)
- Cache PR timeline results (not in scope)
- Batch queries for multiple issues (not in scope)

---

## Success Metrics

### Code Quality
- ✅ pytest: 100% pass rate (48+ tests)
- ✅ mypy: No type errors
- ✅ pylint: Score ≥9.0/10

### Functionality
- ✅ Primary path works (linkedBranches)
- ✅ Fallback path works (PR timeline)
- ✅ Error handling works (multiple PRs, none found)
- ✅ Coordinator integration works

### Maintainability
- ✅ Code follows existing patterns
- ✅ Comprehensive test coverage
- ✅ Clear documentation
- ✅ Simple design (KISS)

---

## Detailed Step Documents

Each step has a dedicated detailed document:

1. **`pr_info/steps/summary.md`** - Architectural overview
2. **`pr_info/steps/step_1.md`** - Test suite creation (TDD)
3. **`pr_info/steps/step_2.md`** - Method implementation
4. **`pr_info/steps/step_3.md`** - Coordinator integration
5. **`pr_info/steps/step_4.md`** - Quality verification
6. **`pr_info/steps/Decisions.md`** - Implementation decisions from plan review

Each step document includes:
- WHERE: File locations and line numbers
- WHAT: Functions and signatures
- HOW: Integration points
- ALGORITHM: Pseudocode logic
- DATA: Input/output structures
- LLM PROMPT: Ready-to-use prompt for implementation

---

## Ready to Execute? 🚀

Start with:
```bash
# Read the summary first
cat pr_info/steps/summary.md

# Then execute steps in order
cat pr_info/steps/step_1.md  # TDD: Create tests
cat pr_info/steps/step_2.md  # Implement method
cat pr_info/steps/step_3.md  # Integrate coordinator
cat pr_info/steps/step_4.md  # Quality checks
```

Each step is self-contained with clear instructions and verification criteria.

**Good luck!** 🎯
