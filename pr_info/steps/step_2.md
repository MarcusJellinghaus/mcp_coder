# Step 2: Verify and fix stale doc references

**Ref:** [summary.md](summary.md) — Items #1, #2, #3

## Context

The issue claims three doc files have stale references from the github_operations migration. However, at planning time all referenced paths still existed. **Each reference must be re-verified before changing.**

## Verification-first approach

For each item below:
1. Check if the referenced file/path **still exists**
2. If it exists and is correct → **skip** (not stale)
3. If it no longer exists → find the correct replacement path and update

## Item #1 — `docs/getting-started/label-setup.md` (line 92)

**WHERE:** `docs/getting-started/label-setup.md` line 92

**Current content:**
```python
python -c "from mcp_coder.utils.github_operations.label_config import get_labels_config_path; print(get_labels_config_path(None))"
```

**Verify:** Does `src/mcp_coder/utils/github_operations/label_config.py` exist and export `get_labels_config_path`?
- If **yes** → skip, reference is correct
- If **no** → search for `get_labels_config_path` in the codebase, update the import path

## Item #2 — `docs/architecture/architecture.md`

**WHERE:** `docs/architecture/architecture.md` — search for all occurrences of `github_operations`

**Verify:** Does `src/mcp_coder/utils/github_operations/` exist as an active package?
- If **yes** → check each specific reference (directory paths, test paths) for accuracy
- If **no** → update references to the new location

**Known references in architecture.md (from planning read):**
- Line 245: `utils/github_operations/` listed in Building Block View with `(tests: utils/github_operations/test_*.py)`
- Multiple sub-module listings (base_manager.py, github_utils.py, issues/, labels_manager.py, pr_manager.py)

For each, verify the file still exists at the referenced path.

## Item #3 — `docs/tests/issues.md`

**WHERE:** `docs/tests/issues.md` — Issue #010 section

**Current content references:**
```
tests/utils/github_operations/test_github_utils.py::TestPullRequestManagerIntegration::test_list_pull_requests_with_filters
```

**Verify:** Does `tests/utils/github_operations/test_github_utils.py` exist and contain `TestPullRequestManagerIntegration`?
- If **yes** → skip, reference is correct
- If **no** → find where `TestPullRequestManagerIntegration` lives now and update the path

## Verification

After all edits (if any):
```
mcp__tools-py__run_pylint_check()
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check()
```

Quality checks are a formality here (doc-only changes won't affect them) but required per CLAUDE.md.

## LLM Prompt

> Read the summary at `pr_info/steps/summary.md` and this step at `pr_info/steps/step_2.md`.
>
> For each of the three doc files listed, **verify first** whether the referenced path is actually stale:
> 1. Check if `src/mcp_coder/utils/github_operations/label_config.py` exists with `get_labels_config_path`
> 2. Check if `src/mcp_coder/utils/github_operations/` still has the sub-modules listed in `architecture.md`
> 3. Check if `tests/utils/github_operations/test_github_utils.py` exists with `TestPullRequestManagerIntegration`
>
> Only update references that are confirmed stale. If a path still exists and is correct, skip it and note "verified — still valid" in the commit message. Run all three quality checks after any edits.
