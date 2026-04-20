# Step 2: Fix the merge-base distance algorithm

> **Context**: See `pr_info/steps/summary.md` for the full issue summary.

## Goal

Apply the algorithm fix in `parent_branch_detection.py`. After this step, all tests from step 1 must pass.

## WHERE

- **Modified**: `src/mcp_coder/utils/git_operations/parent_branch_detection.py`

## WHAT

Five mechanical changes to `detect_parent_branch_via_merge_base()`:

### 1. Add import

Add `get_default_branch_name` import from `.branch_queries`.

### 2. Reverse distance measurement (2 locations)

**Local branches loop (~line 78)** and **remote branches loop (~line 118)**: change `iter_commits` range.

```python
# OLD (measures merge_base → candidate HEAD):
distance = sum(1 for _ in repo.iter_commits(f"{merge_base.hexsha}..{branch.commit.hexsha}"))

# NEW (measures merge_base → current HEAD):
distance = sum(1 for _ in repo.iter_commits(f"{merge_base.hexsha}..{current_commit.hexsha}"))
```

For remote branches, replace `{ref.commit.hexsha}` with `{current_commit.hexsha}`.

### 3. Remove early-exit blocks (2 locations)

Delete both `if distance == 0: return branch.name` blocks (local ~lines 88-93, remote ~lines 128-133). With the new metric, distance=0 can occur for multiple candidates. Let them all be collected and sorted.

### 4. Add default-branch tiebreaker to sort

Before the candidate loop, resolve the default branch name:

```python
default_branch = get_default_branch_name(project_dir)
```

Change the final sort from:

```python
candidates_passing.sort(key=lambda x: x[1])
```

to:

```python
candidates_passing.sort(key=lambda x: (x[1], 0 if x[0] == default_branch else 1))
```

### 5. Update docstring and inline comments

Update text that references the old distance direction:

- **Docstring** (lines ~23-27): Change "closest to the merge-base" / "candidate branch HEAD" to reflect the new direction (merge-base → current HEAD).
- **Threshold docstring** (lines ~32-34): Change "candidate branch HEAD" to "current branch HEAD".
- **Local branch comment** (line ~77): Update "Count commits from merge-base to branch HEAD" → "Count commits from merge-base to current HEAD".
- **Remote branch comment** (line ~133): Same update as local.
- **Module docstring** (lines ~3-6): Update if it references the old direction.

## ALGORITHM

```python
def detect_parent_branch_via_merge_base(project_dir, current_branch, threshold=20):
    default_branch = get_default_branch_name(project_dir)
    current_commit = repo.heads[current_branch].commit
    for each candidate branch (local + remote, skipping current):
        merge_base = repo.merge_base(current_commit, candidate.commit)
        distance = count(merge_base..current_commit)  # REVERSED from old code
        if distance <= threshold:
            candidates.append((name, distance))
    candidates.sort(key=(distance, 0 if name == default_branch else 1))
    return candidates[0].name if candidates else None
```

## DATA

- No changes to function signature, return type, or exports
- `MERGE_BASE_DISTANCE_THRESHOLD` stays at 20
- No changes to `__init__.py` exports

## Commit message

```
fix(base-branch): reverse merge-base distance to measure toward current HEAD (#803)
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Edit src/mcp_coder/utils/git_operations/parent_branch_detection.py with the
four changes described in step_2.md:

1. Add `from .branch_queries import get_default_branch_name` to imports
2. In both loops (local and remote), change iter_commits range from
   `merge_base..candidate_HEAD` to `merge_base..current_HEAD`
3. Delete both `if distance == 0: return` early-exit blocks
4. Add `default_branch = get_default_branch_name(project_dir)` before the loops,
   and change the sort key to `(x[1], 0 if x[0] == default_branch else 1)`
5. Update the function docstring, threshold docstring, and inline comments
   (lines ~23-27, ~32-34, ~77, ~133, and module docstring ~3-6) to reflect
   the new distance direction (merge_base → current_HEAD, not candidate_HEAD)

After editing, run pylint, mypy, and pytest (unit tests only).
All tests must pass, including the new tests from step 1.
```
