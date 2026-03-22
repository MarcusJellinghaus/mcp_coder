# Step 7: src/ W0212 — protected-access inline-disables (11 occurrences)

## Goal
Add inline pylint disables for protected-access warnings where no public API exists.

## WHERE — Files Modified

**`src/mcp_coder/utils/git_operations/core.py`** — `_close_repo_safely()` (5 accesses):
Add block-level disable/enable around the `_proc` access block:
```python
# pylint: disable=protected-access  # GitPython has no public API for process cleanup
if hasattr(repo, "git") and hasattr(repo.git, "_proc") and repo.git._proc:
    ...
# pylint: enable=protected-access
```

**`src/mcp_coder/utils/github_operations/issues/branch_manager.py`** (5 accesses):
Add inline disable on each `_Github__requester` access line:
```python
_, result = self._github_client._Github__requester.graphql_query(  # pylint: disable=protected-access  # no public GraphQL API in PyGithub
```

**`src/mcp_coder/cli/commands/coordinator/core.py`** (1 access):
```python
jenkins_base_url = jenkins_client._client.server.rstrip("/")  # pylint: disable=protected-access  # python-jenkins has no public server URL accessor
```

## DATA

Pylint count reduced by: **11 warnings**.

## TDD Note

Comments only — no logic change. Run existing tests to confirm.

---

## LLM Prompt

```
Please implement Step 7: fix W0212 (protected-access) in src/.
See pr_info/steps/step_7.md for exact locations.
Rules: add inline or block-level disable comments. No code changes.
Run pylint, pytest (fast unit tests), and mypy to verify.
```
