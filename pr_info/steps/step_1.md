# Step 1: Enhance `branch_manager.py` — Core Resolution Logic

> **Context**: Read `pr_info/steps/summary.md` for architectural overview of issue #264.

## Goal

Extend `IssueBranchManager` in `branch_manager.py` with closed-PR fallback, branch pattern search, and multiple-linked-branches handling. This step is self-contained — no callers change yet.

## Approach: TDD

Write tests first in `test_branch_resolution.py`, then implement the production code.

---

## Part A: Generalize `_extract_open_prs()` → `_extract_prs_by_states()`

### WHERE
- **Test**: `tests/utils/github_operations/issues/test_branch_resolution.py`
- **Prod**: `src/mcp_coder/utils/github_operations/issues/branch_manager.py`

### WHAT — Signature change
```python
# OLD
@staticmethod
def _extract_open_prs(timeline_items: List[dict[str, Any]]) -> List[dict[str, Any]]:

# NEW
@staticmethod
def _extract_prs_by_states(
    timeline_items: List[dict[str, Any]],
    states: set[str],
) -> List[dict[str, Any]]:
```

### ALGORITHM
```
for each node in timeline_items:
    skip if not CrossReferencedEvent
    skip if source missing state or headRefName
    if source["state"] in states: add to results
return results
```

### HOW
- Rename the method and add `states` parameter
- Update the single internal call site in `get_branch_with_pr_fallback()`:
  - `self._extract_open_prs(timeline_items)` → `self._extract_prs_by_states(timeline_items, {"OPEN"})`

### TESTS to write
1. `test_extract_prs_by_states_open_only` — filters OPEN, excludes CLOSED/MERGED (mirrors existing `_extract_open_prs` tests)
2. `test_extract_prs_by_states_closed_only` — filters CLOSED, excludes OPEN/MERGED
3. `test_extract_prs_by_states_multiple_states` — `{"OPEN", "CLOSED"}` returns both

---

## Part B: Add `_search_branches_by_pattern()` method

### WHERE
- **Test**: `tests/utils/github_operations/issues/test_branch_resolution.py`
- **Prod**: `src/mcp_coder/utils/github_operations/issues/branch_manager.py`

### WHAT — New method signature
```python
def _search_branches_by_pattern(
    self,
    issue_number: int,
    repo: Any,  # github.Repository.Repository
) -> str | None:
```

### ALGORITHM
```
# Pass 1: prefix match (cheap, catches "123-foo" style)
refs = repo.get_git_matching_refs(f"heads/{issue_number}")
pattern = re.compile(r"(^|/)" + str(issue_number) + r"[-_]")
matches = [ref.ref.removeprefix("refs/heads/") for ref in refs if pattern.search(ref.ref.removeprefix("refs/heads/"))]
if len(matches) == 1: log INFO, return matches[0]
if len(matches) > 1: log WARNING (ambiguous), return None

# Pass 2: full scan fallback (catches "feature/123-foo" style)
refs = repo.get_git_matching_refs("heads/")
branches = collect up to 500 refs (log warning if more)
matches = [ref.ref.removeprefix("refs/heads/") for ref in branches if pattern.search(branch_name)]
if len(matches) == 1: log INFO, return matches[0]
if len(matches) > 1: log WARNING (ambiguous), return None
return None  # no match
```

### DATA
- Input: issue number, PyGithub `Repository` object
- Output: branch name `str` or `None`
- Uses `repo.get_git_matching_refs("heads/")` which returns a paginated list of `GitRef` objects
- Each `GitRef` has `.ref` attribute like `"refs/heads/feature/252-foo"`

### TESTS to write
1. `test_search_branches_no_match` — empty refs list → `None`
2. `test_search_branches_single_match_prefix` — prefix pass finds `252-bar` → returns branch name (no full scan needed)
3. `test_search_branches_single_match_nested` — prefix pass empty, full scan finds `feature/252-foo` → returns branch name
4. `test_search_branches_multiple_matches` — two matching refs → `None` (ambiguous)
5. `test_search_branches_500_cap` — 501 refs in full scan → processes first 500, logs warning
6. `test_search_branches_pattern_variations` — matches `feature/252-foo`, `252-bar`, `fix/252_baz`; does NOT match `1252-foo`, `252` (no separator)

---

## Part C: Extend `get_branch_with_pr_fallback()` with new resolution steps

### WHERE
- **Test**: `tests/utils/github_operations/issues/test_branch_resolution.py`
- **Prod**: `src/mcp_coder/utils/github_operations/issues/branch_manager.py`

### WHAT — Updated resolution order inside `get_branch_with_pr_fallback()`

The method signature stays the same:
```python
def get_branch_with_pr_fallback(
    self, issue_number: int, repo_owner: str, repo_name: str
) -> Optional[str]:
```

### ALGORITHM (full updated flow)
```
# Step 1: linkedBranches (CHANGED: multiple = ambiguous)
linked = self.get_linked_branches(issue_number)
if len(linked) == 1: return linked[0]
if len(linked) > 1: log warning, return None  # NEW: was returning linked[0]

# Step 2: Open PRs from timeline (UNCHANGED)
open_prs = self._extract_prs_by_states(timeline_items, {"OPEN"})
if len(open_prs) == 1: return headRefName
if len(open_prs) > 1: log warning, return None

# Step 3: Closed (not merged) PRs (NEW)
closed_prs = self._extract_prs_by_states(timeline_items, {"CLOSED"})
closed_prs.sort(key=lambda pr: pr["number"], reverse=True)  # most recent first
branch_checks = 0
for pr in closed_prs:
    if branch_checks >= 25: break
    branch_checks += 1
    try:
        repo.get_branch(pr["headRefName"])  # verify exists
        return pr["headRefName"]
    except GithubException:
        continue  # branch deleted

# Step 4: Branch pattern search (NEW)
return self._search_branches_by_pattern(issue_number, repo)
```

### HOW — Integration details
- `repo` object: already available from `self._get_repository()` call at the top of the method
- Closed-PR branch verification: use `repo.get_branch(name)` — raises `GithubException` (404) if branch doesn't exist
- Import `GithubException` from `github` package (already used elsewhere in codebase)
- The timeline GraphQL query already fetches both OPEN and CLOSED PRs in the response — we just weren't filtering for CLOSED before

### TESTS to write

**Multiple linked branches:**
1. `test_multiple_linked_branches_returns_none` — 2 linked branches → `None` (was: returned first)

**Closed PR fallback:**
2. `test_closed_pr_with_existing_branch` — closed PR, branch exists → returns branch name
3. `test_closed_pr_with_deleted_branch` — closed PR, `get_branch` raises → `None`
4. `test_merged_pr_not_matched` — merged PR in timeline → skipped (state is MERGED, not CLOSED)
5. `test_closed_pr_25_check_cap` — 30 closed PRs, all branches deleted → stops after 25 checks
6. `test_closed_pr_most_recent_preferred` — multiple closed PRs with existing branches → returns highest PR number
7. `test_closed_pr_prefers_open_pr` — both open and closed PRs exist → returns open PR branch (order)

**Pattern search integration:**
7. `test_pattern_fallback_used_when_no_prs` — no linked branches, no PRs → pattern search called
8. `test_pattern_fallback_not_called_when_linked_branch_found` — linked branch exists → pattern search NOT called

---

## LLM Prompt for Step 1

```
You are implementing Step 1 of issue #264 for the mcp-coder project.
Read pr_info/steps/summary.md for full context, then read this step file (pr_info/steps/step_1.md).

Read the current production file: src/mcp_coder/utils/github_operations/issues/branch_manager.py
Read the current test file: tests/utils/github_operations/issues/test_branch_resolution.py

Follow TDD: for each Part (A, B, C), write the tests first, then implement the production code.
Run tests after each part to verify.

Key constraints:
- _extract_prs_by_states replaces _extract_open_prs (rename, don't add alongside)
- _search_branches_by_pattern is a new instance method (needs self for logging)
- get_branch_with_pr_fallback signature does NOT change
- Use repo.get_branch() for closed-PR verification (raises GithubException on 404)
- Use repo.get_git_matching_refs("heads/") for pattern search
- Pattern regex: r"(^|/)" + str(issue_number) + r"[-_]"
- Log at INFO when pattern match found, WARNING when ambiguous
```
