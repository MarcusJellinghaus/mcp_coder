# Summary: Enable and Clean Up Pylint Warnings (#493)

## Overview

This PR enables pylint W-category warnings for both `src/` and `tests/` by fixing or
inline-disabling all existing occurrences, then updating `pyproject.toml` as the final
commit so CI stays green throughout.

**No new files are created. No logic changes. Pure lint cleanup.**

---

## Architectural / Design Changes

None. This is exclusively a lint-hygiene PR. The approach for each warning type:

| Pattern | Decision | Rationale |
|---------|----------|-----------|
| Unused imports / variables | **Remove** | Dead code; zero risk |
| Unused arguments | **Rename to `_`** | Preserves API contract, signals intent |
| `raise X` inside `except` without `from e` | **Add `from e`** | Proper exception chaining; no behaviour change |
| F-string without interpolation | **Remove `f` prefix** | Trivial fix |
| Broad exception raised (`raise Exception`) | **Use `RuntimeError`** | Minimal specific type |
| Try-except-raise (W0706) | **Add inline disable** | Intentional re-raise pattern for subprocess isolation |
| Deprecated `onerror=` arg (W4903) | **Replace with `onexc=`** | Forward-compatible Python 3.12 |
| Protected-access (W0212, `src/` only) | **Add inline disable per line** | Third-party API workaround already documented in comments; no public API exists |
| Global statements (W0603) | **Add inline disable per line** | Module-level singletons; `lru_cache` would break test resets |
| Broad-except (W0718, `src/`) | **Inline disable with justification** | Intentional catch-all boundaries; adding TODO where narrowing is possible |
| `tests/` W0212, W0613, W0611, W0404 | **Per-file-ignores in config** | Standard pytest patterns; not code quality issues |
| `tests/` W0621 | **Global disable in config** | Pytest fixture redefined-outer-name; already intended |
| W0511 (fixme/TODO) | **Global disable in config** | Informational only |
| W1203 (logging f-string) | **Global disable in config** | Project deliberately uses f-strings for readability |

---

## Files Modified

### `src/`

| File | Warning(s) Fixed |
|------|-----------------|
| `src/mcp_coder/cli/commands/create_pr.py` | W0611 |
| `src/mcp_coder/cli/commands/implement.py` | W0611 |
| `src/mcp_coder/cli/commands/prompt.py` | W0611 |
| `src/mcp_coder/cli/commands/help.py` | W0613 |
| `src/mcp_coder/cli/commands/verify.py` | W1309 |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | W0611 |
| `src/mcp_coder/cli/commands/coordinator/core.py` | W0611, W0613, W0212 |
| `src/mcp_coder/cli/main.py` | W0613 |
| `src/mcp_coder/cli/parsers.py` | W0707 |
| `src/mcp_coder/llm/mlflow_logger.py` | W0611, W0603, W0718 |
| `src/mcp_coder/llm/mlflow_metrics.py` | W0718 |
| `src/mcp_coder/llm/providers/claude/claude_code_api.py` | W0611 |
| `src/mcp_coder/llm/providers/claude/claude_cli_verification.py` | W0612 |
| `src/mcp_coder/llm/providers/langchain/agent.py` | W0611, W0613 |
| `src/mcp_coder/prompt_manager.py` | W0612, W0707, W0718 |
| `src/mcp_coder/checks/branch_status.py` | W0612, W0718 |
| `src/mcp_coder/cli/commands/check_branch_status.py` | W0612, W0718 |
| `src/mcp_coder/cli/commands/commit.py` | W0718 |
| `src/mcp_coder/cli/commands/create_plan.py` | W0718 |
| `src/mcp_coder/cli/commands/define_labels.py` | W0718 |
| `src/mcp_coder/cli/commands/gh_tool.py` | W0718 |
| `src/mcp_coder/cli/commands/git_tool.py` | W0718 |
| `src/mcp_coder/cli/commands/set_status.py` | W0718 |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | W0718 |
| `src/mcp_coder/utils/mlflow_config_loader.py` | W0611 |
| `src/mcp_coder/utils/folder_deletion.py` | W0613 |
| `src/mcp_coder/utils/timezone_utils.py` | W0707 |
| `src/mcp_coder/utils/git_operations/branches.py` | W0611 |
| `src/mcp_coder/utils/git_operations/commits.py` | W0611 |
| `src/mcp_coder/utils/git_operations/core.py` | W0611, W0212 |
| `src/mcp_coder/utils/git_operations/diffs.py` | W0611 |
| `src/mcp_coder/utils/git_operations/file_tracking.py` | W0611 |
| `src/mcp_coder/utils/git_operations/readers.py` | W0612 |
| `src/mcp_coder/utils/git_operations/staging.py` | W0611 |
| `src/mcp_coder/utils/github_operations/pr_manager.py` | W0611 |
| `src/mcp_coder/utils/github_operations/issues/branch_manager.py` | W0212 |
| `src/mcp_coder/utils/subprocess_runner.py` | W0706 |
| `src/mcp_coder/utils/subprocess_runner.py` | W0706 |
| `src/mcp_coder/workflows/create_plan.py` | W0613 |
| `src/mcp_coder/workflows/implement/core.py` | W0611 |
| `src/mcp_coder/workflows/implement/task_processing.py` | W0707, W0719 |
| `src/mcp_coder/workflows/vscodeclaude/cleanup.py` | W0611 |
| `src/mcp_coder/workflows/vscodeclaude/issues.py` | W0611 |
| `src/mcp_coder/workflows/vscodeclaude/session_launch.py` | W0611, W0613, W4903 |
| `src/mcp_coder/workflows/vscodeclaude/sessions.py` | W0603 |
| `src/mcp_coder/workflows/vscodeclaude/status.py` | W0611 |
| `src/mcp_coder/workflows/vscodeclaude/workspace.py` | W4903 |
| `src/mcp_coder/__init__.py` | W0718 |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | W0718 |

### `tests/`

All test file changes are in the same commit (step 4):

| File | Warning(s) Fixed |
|------|-----------------|
| `tests/workflows/vscodeclaude/test_cleanup.py` | W0612 (14× tuple unpack `session, git_status`) |
| `tests/cli/commands/test_define_labels.py` | W0612 (`repo` unused) |
| `tests/cli/commands/test_check_branch_status_ci_waiting.py` | W0612 (`ci_status`) |
| `tests/cli/commands/test_commit.py` | W0612 (`captured_out`) |
| `tests/cli/commands/test_gh_tool.py` | W0612 (`result`) |
| `tests/cli/commands/test_verify_integration.py` | W0612 (`call_args`) |
| `tests/formatters/test_integration.py` | W0612 (`i`) |
| `tests/llm/test_mlflow_logger.py` | W0612 (`logger`, `result`) |
| `tests/llm/providers/claude/test_claude_cli_stream_integration.py` | W0612 (`result`) |
| `tests/llm/session/test_resolver.py` | W0612 (`fake_path`) |
| `tests/utils/test_folder_deletion.py` | W0612 (`mock_move`) |
| `tests/utils/git_operations/test_commits.py` | W0612 (`repo`) |
| `tests/utils/git_operations/test_remotes.py` | W0612 (`expected_sha`) |
| `tests/workflows/test_create_pr_integration.py` | W0612 (`repo`) |
| `tests/workflows/vscodeclaude/test_closed_issues_integration.py` | W0612 (`mock_launch`, `result`) |
| `tests/workflows/vscodeclaude/test_issues.py` | W0612 (`issues_without_branch`) |
| `tests/workflows/vscodeclaude/test_orchestrator_sessions.py` | W0612 (`mock_execute`) |
| `tests/utils/github_operations/test_base_manager.py` | W0718 |
| Multiple test files | W1514 (add `encoding="utf-8"` to `open()`) |
| Multiple test files | W1404, W0108, W0107, W0702, W0201, W0719 |

### Config (last)

| File | Change |
|------|--------|
| `pyproject.toml` | Replace `disable = ["W", "C", "R"]` with selective disables + per-file-ignores |

---

## Commit Order (CI-safe)

1. **Step 1** — `src/` removals: W0611, W0612, W0613, W1309 (pure deletions/renames)
2. **Step 2** — `src/` mechanical fixes: W0707, W0719, W4903, W0706
3. **Step 3** — `src/` inline-disables: W0603, W0212, W0718
4. **Step 4** — `tests/` all fixes: W0612, W0718, W1514, W1404, W0108, W0107, W0702, W0201, W0719
5. **Step 5** — `pyproject.toml` config change (enables warnings in CI)
