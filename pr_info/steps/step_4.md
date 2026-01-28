# Step 4: Fix Failing Integration Test

## LLM Prompt

```
Read pr_info/steps/summary.md for context. Implement Step 4: Fix the failing integration test for git push force-with-lease.

This step investigates and fixes the test_git_push_force_with_lease_fails_on_unexpected_remote test.
```

## WHERE: File Paths

- `tests/utils/git_operations/test_remotes.py`
- `src/mcp_coder/utils/git_operations/remotes.py` (if behavior fix needed)

## WHAT: The Failing Test

```python
def test_git_push_force_with_lease_fails_on_unexpected_remote(
    self, git_repo_with_remote: tuple[Repo, Path, Path], tmp_path: Path
) -> None:
    """Test force with lease fails if remote has unexpected commits."""
    # ... setup creates another clone that pushes to remote ...
    
    # force_with_lease should fail because remote has unexpected commits
    result = git_push(project_dir, force_with_lease=True)

    # Should fail safely
    assert result["success"] is False  # FAILS: gets True
    assert result["error"] is not None
```

## INVESTIGATION NEEDED

### Hypothesis 1: Fetch Updates Local Refs

The test creates changes in another clone and pushes them. However, if `git_push` internally does a fetch before push, the local refs would be updated and force-with-lease would succeed.

Check `git_push` implementation in `remotes.py`.

### Hypothesis 2: Git Version Difference

Different git versions may handle force-with-lease differently. CI might be using a newer git version.

### Hypothesis 3: Timing/Race Condition

The test may have a timing issue where the push happens before the other clone's push is visible.

## HOW: Investigation Steps

1. Read `src/mcp_coder/utils/git_operations/remotes.py` to understand `git_push` behavior
2. Check if it does a fetch before push
3. If fetch is the issue, the test expectation may be wrong (force-with-lease is working correctly)
4. Determine if this is a test bug or implementation bug

## ALGORITHM: Potential Fixes

### If Test Expectation is Wrong
The test expects force-with-lease to fail, but if the implementation fetches first, force-with-lease correctly succeeds because local refs are updated.

Fix: Update test to NOT expect failure, OR modify test to ensure local refs are stale.

### If Implementation is Wrong
If `git_push` should NOT fetch before force-with-lease push (to preserve safety semantics):

Fix: Modify `git_push` to skip fetch when `force_with_lease=True`.

## DATA: Expected Behavior

Force-with-lease should:
- Fail if remote ref doesn't match local's expected value
- Succeed if refs match (even after fetch updates them)

The question is: **Should git_push fetch before pushing?**

## Success Criteria

- [ ] Root cause identified
- [ ] Test or implementation fixed appropriately
- [ ] Integration tests pass
- [ ] Behavior documented if changed
