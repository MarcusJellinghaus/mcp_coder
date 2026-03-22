# Step 8: src/ W0718 — broad-exception-caught inline-disables (181 occurrences)

## Goal
Add inline pylint disables for all `except Exception` clauses in `src/`.
Each disable includes a justification comment.

## WHERE — Files Modified

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

```python
except Exception:  # pylint: disable=broad-exception-caught  # <justification tag>
```
or (when exception variable is used):
```python
except Exception as e:  # pylint: disable=broad-exception-caught  # <justification tag>
```

## DATA

Pylint count reduced by: **181 warnings**.

## TDD Note

Comments only — no logic change. Run existing tests to confirm.

---

## LLM Prompt

```
Please implement Step 8: fix W0718 (broad-exception-caught) in src/.
See pr_info/steps/step_8.md for exact files and justification tags.
Rules: append inline disable comment with justification to each `except Exception` line.
No code changes. Run pylint, pytest (fast unit tests), and mypy to verify.
```
