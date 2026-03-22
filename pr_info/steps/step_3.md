# Step 3: Fix `src/` inline-disables — W0603, W0212, W0718

## Goal
Silence the remaining `src/` warnings that cannot be mechanically fixed without
introducing risk or behaviour change. Each inline-disable includes a justification
comment. No logic changes.

---

## WHERE — Files Modified

**W0603 — global-statement (7 occurrences, 2 files):**

`src/mcp_coder/llm/mlflow_logger.py`:
- `is_mlflow_available()` line 49: `global _mlflow_available`
- `get_mlflow_logger()` line 702: `global _global_logger`

`src/mcp_coder/workflows/vscodeclaude/sessions.py`:
- `_get_vscode_processes()` line 135: `global _vscode_process_cache`
- `clear_vscode_process_cache()` line 174: `global _vscode_process_cache`
- `_get_vscode_pids()` line 192: `global _vscode_pid_cache`
- `_get_vscode_window_titles()` line 222: `global _vscode_window_cache`
- `clear_vscode_window_cache()` line 270: `global _vscode_window_cache`

**W0212 — protected-access (11 occurrences, 3 files):**

`src/mcp_coder/utils/git_operations/core.py` — `_close_repo_safely()`:
- 5 accesses to `repo.git._proc` (lines 40, 42, 43, 47, 48)

`src/mcp_coder/utils/github_operations/issues/branch_manager.py`:
- 4 accesses to `self._github_client._Github__requester` (lines 280, 395, 585, 734)
- 1 access to `self._github_client._Github__requester` (line 765, `_, _ = ...` assignment)

`src/mcp_coder/cli/commands/coordinator/core.py` — `dispatch_workflow()`:
- 1 access to `jenkins_client._client.server` (line 472)

**W0718 — broad-exception-caught (181 occurrences across many files):**

Files and justification categories:

| File | Count | Justification tag |
|------|-------|-------------------|
| `src/mcp_coder/llm/mlflow_logger.py` | 11 | `# mlflow graceful-degradation — optional dependency` |
| `src/mcp_coder/llm/mlflow_metrics.py` | 2 | `# mlflow graceful-degradation — optional dependency` |
| `src/mcp_coder/checks/branch_status.py` | 5 | `# TODO: narrow when GitHub/CI exception types are stable` |
| `src/mcp_coder/cli/commands/check_branch_status.py` | 6 | `# TODO: narrow to specific GitHub/CI exceptions` |
| `src/mcp_coder/cli/commands/commit.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/create_plan.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/create_pr.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/define_labels.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/gh_tool.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/git_tool.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/implement.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/prompt.py` | 3 | `# top-level CLI error boundary` / `# mlflow graceful-degradation` |
| `src/mcp_coder/cli/commands/set_status.py` | 2 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | 5 | `# TODO: narrow per sub-workflow error types` |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/cli/main.py` | 1 | `# top-level CLI error boundary` |
| `src/mcp_coder/prompt_manager.py` | 3 | `# TODO: narrow to specific file/path exceptions` |
| `src/mcp_coder/utils/git_operations/branches.py` | 1 | `# TODO: narrow to GitCommandError` |
| `src/mcp_coder/utils/git_operations/readers.py` | ~5 | `# TODO: narrow to GitCommandError` |
| `src/mcp_coder/__init__.py` | 1 | `# optional import fallback — broad catch intentional` |
| All remaining `src/` workflow files | remainder | `# TODO: narrow exception type` |

## WHAT

**Format for all W0603 disables:**
```python
global _some_var  # pylint: disable=global-statement  # module-level singleton
```

**Format for all W0212 disables:**

For `_close_repo_safely` in `core.py` — add a single block-level disable before the
`if hasattr(repo.git, "_proc")` check, and a block-level re-enable after:
```python
# pylint: disable=protected-access  # GitPython has no public API for process cleanup
if hasattr(repo, "git") and hasattr(repo.git, "_proc") and repo.git._proc:
    ...
# pylint: enable=protected-access
```

For `branch_manager.py` — add inline disable on each `_Github__requester` access line:
```python
_, result = self._github_client._Github__requester.graphql_query(  # pylint: disable=protected-access  # no public GraphQL API in PyGithub
```

For `coordinator/core.py` line 472:
```python
jenkins_base_url = jenkins_client._client.server.rstrip("/")  # pylint: disable=protected-access  # python-jenkins has no public server URL accessor
```

**Format for all W0718 disables:**
```python
except Exception:  # pylint: disable=broad-exception-caught  # <justification tag>
```
or (when exception variable is used):
```python
except Exception as e:  # pylint: disable=broad-exception-caught  # <justification tag>
```

## HOW

No integration points change. All changes are purely comment additions on existing lines.
The `# pylint: disable=` comment applies to exactly the line it is on (inline form).

For the block-level W0212 disable in `core.py`, the `# pylint: enable=protected-access`
restores the default after the block.

## ALGORITHM

```
For W0603 (7 locations):
    Append  # pylint: disable=global-statement  # module-level singleton
    to each `global <var>` line

For W0212 (11 locations):
    core.py: add block disable/enable around the _proc access block
    branch_manager.py: add inline disable on each of the 5 _Github__requester lines
    coordinator/core.py: add inline disable on the _client.server line

For W0718 (181 locations):
    For each `except Exception` or `except Exception as e`:
        Append  # pylint: disable=broad-exception-caught  # <justification>
    Use justification from the table above based on which file/function it is in
    Use TODO: prefix where future narrowing is possible
```

## DATA

No return value changes. No type changes.
Pylint count reduced by: 7 + 11 + 181 = **199 warnings** in `src/`.

## TDD Note

No new tests needed — comments do not affect behaviour.
Run full pylint on `src/` after this step and confirm W0603, W0212, W0718 are all zero.
Run pytest to confirm no regressions.

---

## LLM Prompt

```
Please implement Step 3 of the pylint warning cleanup described in
`pr_info/steps/summary.md` and `pr_info/steps/step_3.md`.

This step adds inline pylint-disable comments for W0603 (global-statement),
W0212 (protected-access), and W0718 (broad-exception-caught) in `src/`.

Rules:
- W0603: Append `# pylint: disable=global-statement  # module-level singleton`
  to each of the 7 `global <var>` lines in mlflow_logger.py and sessions.py.
- W0212: Three files:
  * core.py (_close_repo_safely): add block-level disable/enable around the
    _proc access section with comment `# GitPython has no public API for process cleanup`
  * branch_manager.py: add inline disable on each _Github__requester access line
    with comment `# no public GraphQL API in PyGithub`
  * coordinator/core.py: add inline disable on the jenkins_client._client.server line
    with comment `# python-jenkins has no public server URL accessor`
- W0718: For each of the 181 `except Exception` clauses in src/, append
  `# pylint: disable=broad-exception-caught  # <justification>`
  Use the justification table in step_3.md to pick the right tag per file.
  Use `# TODO: narrow ...` prefix where future narrowing is feasible.
- Do NOT change any logic
- Run pylint src/ (--disable=C,R,W1203 --enable=W) to verify zero remaining
  W0603, W0212, W0718 warnings
- Run pytest (fast unit tests) and mypy to confirm no regressions
```
