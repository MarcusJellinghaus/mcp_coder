# Step 2: Change `core.py` wrapper to return `(result, error_msg)` tuple

> **Context**: See `pr_info/steps/summary.md` for full issue context. Step 1 must be completed first.

## LLM Prompt

You are implementing Step 2 of Issue #859. Read `pr_info/steps/summary.md` for context, then implement this step.

**Goal**: Change `create_pull_request()` in `core.py` to return a tuple `(PullRequestData | None, str | None)` so error messages propagate to callers. Update the wrapper's unit tests in `test_repository.py` accordingly.

## WHERE

- **Modify**: `src/mcp_coder/workflows/create_pr/core.py` — function `create_pull_request()`
- **Modify**: `tests/workflows/create_pr/test_repository.py` — class `TestCreatePullRequest`

## WHAT

### `core.py` `create_pull_request()` wrapper (~line 344):

**Change return type** from `PullRequestData | None` to `tuple[PullRequestData | None, str | None]`.

**Change each failure path** to return `(None, "error message")`:

| Current | New |
|---|---|
| `return None` after `current_branch is None` | `return None, "Could not determine current branch"` |
| `return None` after `base_branch is None` | `return None, "Could not detect base branch for PR creation"` |
| `return None` after `not pr_result or not pr_result.get("number")` | `return None, "Failed to create pull request"` |
| `return None` in `except Exception as e` | `return None, f"Error creating pull request: {e}"` |

**Change success path** to return tuple:

| Current | New |
|---|---|
| `return pr_result` | `return pr_result, None` |

**Remove** the `not pr_result or not pr_result.get("number")` check — after Step 1, `pr_manager.create_pull_request()` raises on failure, so it won't return `{}`. The `except` block handles those exceptions. Keep the `except Exception` block to catch both `ValueError` and `GithubException`.

### Updated function signature:

```python
def create_pull_request(
    project_dir: Path, title: str, body: str
) -> tuple[PullRequestData | None, str | None]:
```

## ALGORITHM

```
# Pseudocode for core.py create_pull_request:
current_branch = get_current_branch_name(project_dir)
if current_branch is None: return (None, "Could not determine current branch")
base_branch = detect_base_branch(...)
if base_branch is None: return (None, "Could not detect base branch...")
try:
    pr_manager = PullRequestManager(project_dir)
    pr_result = pr_manager.create_pull_request(...)
    return (pr_result, None)
except Exception as e:
    return (None, f"Error creating pull request: {e}")
```

## DATA

- **Input**: unchanged
- **Output**: `tuple[PullRequestData | None, str | None]`
  - Success: `({"number": 42, "url": "...", ...}, None)`
  - Failure: `(None, "descriptive error message")`

## Test changes

### `tests/workflows/create_pr/test_repository.py` — class `TestCreatePullRequest`:

Update all tests to expect tuples:

| Test | Current assertion | New assertion |
|---|---|---|
| `test_create_pull_request_success` | `assert result is not None; assert result["number"] == 123` | `assert result == ({"number": 123, ...}, None)` — unpack `result, error = create_pull_request(...)`, assert `error is None`, assert `result["number"] == 123` |
| `test_create_pull_request_no_current_branch` | `assert result is None` | `result, error = ...; assert result is None; assert "current branch" in error` |
| `test_create_pull_request_no_parent_branch` | `assert result is None` | `result, error = ...; assert result is None; assert "base branch" in error` |
| `test_create_pull_request_manager_failure` | `mock returns {}; assert result is None` | `mock raises ValueError("test error"); result, error = ...; assert result is None; assert "test error" in error` |
| `test_create_pull_request_no_pr_number` | `mock returns {"url": ...} without number; assert result is None` | Remove this test — after Step 1, `pr_manager.create_pull_request()` raises instead of returning incomplete dicts. The `_manager_failure` and `_exception` tests already cover error paths. |
| `test_create_pull_request_exception` | `assert result is None` | `result, error = ...; assert result is None; assert "GitHub API error" in error` |
| `test_create_pull_request_success_with_url` | `assert result is not None; assert result["number"] == 456` | `result, error = ...; assert error is None; assert result["number"] == 456` |
| `test_create_pull_request_success_without_url` | `assert result is not None; assert result["number"] == 789` | `result, error = ...; assert error is None; assert result["number"] == 789` |

## Commit

```
fix(create-pr): return (result, error_msg) tuple from create_pull_request wrapper

Change core.py create_pull_request() to return a tuple so error messages
propagate to callers instead of being lost. Update test_repository.py
to match new return type.

Part of #859.
```
