## About this repo

`mcp-coder` is a CLI and workflow orchestrator for LLM sessions, using Claude Code or langchain as backend.

## MCP Tools — mandatory

Use MCP tools for **all** operations. Never use `Read`, `Write`, `Edit`, or `Bash` for tasks that have an MCP equivalent. If no MCP equivalent exists, use Bash. Check the tool mapping table below first.

### Tool mapping

| Task | MCP tool |
|------|----------|
| Read file | `mcp__workspace__read_file` |
| Edit file | `mcp__workspace__edit_file` |
| Write file | `mcp__workspace__save_file` |
| Append to file | `mcp__workspace__append_file` |
| Delete file | `mcp__workspace__delete_this_file` |
| Move file | `mcp__workspace__move_file` |
| List directory | `mcp__workspace__list_directory` |
| Search files | `mcp__workspace__search_files` |
| Read reference project | `mcp__workspace__read_reference_file` |
| List reference dir | `mcp__workspace__list_reference_directory` |
| Get reference projects | `mcp__workspace__get_reference_projects` |
| Run pytest | `mcp__tools-py__run_pytest_check` |
| Run pylint | `mcp__tools-py__run_pylint_check` |
| Run mypy | `mcp__tools-py__run_mypy_check` |
| Run vulture | `mcp__tools-py__run_vulture_check` |
| Run lint-imports | `mcp__tools-py__run_lint_imports_check` |
| Run ruff check | `mcp__tools-py__run_ruff_check` |
| Run ruff fix | `mcp__tools-py__run_ruff_fix` |
| Run bandit | `mcp__tools-py__run_bandit_check` |
| Format code (black+isort) | `mcp__tools-py__run_format_code` |
| Get library source | `mcp__tools-py__get_library_source` |
| Refactoring | `mcp__tools-py__move_symbol`, `move_module`, `rename_symbol`, `list_symbols`, `find_references` |
| Git status | `mcp__workspace__git_status` |
| Git diff (includes compact diff) | `mcp__workspace__git_diff` |
| Git log | `mcp__workspace__git_log` |
| Git merge-base | `mcp__workspace__git_merge_base` |
| Git read-only (fetch, ls-tree, show, ls-files, ls-remote, rev-parse, branch list) | `mcp__workspace__git` |
| `gh issue view` | `mcp__workspace__github_issue_view` |
| `gh issue list` | `mcp__workspace__github_issue_list` |
| `gh pr view` | `mcp__workspace__github_pr_view` |
| `gh search` | `mcp__workspace__github_search` |

## Code quality checks

After making code changes, run:

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check
mcp__tools-py__run_mypy_check
```

All checks must pass before proceeding.

**Ruff:** use `mcp__tools-py__run_ruff_check`. Do not call `ruff` directly.

**Pytest:** always use `extra_args: ["-n", "auto"]` for parallel execution.

```python
# Fast unit tests (recommended)
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not langchain_integration and not llm_integration and not textual_integration"])

# Specific integration tests
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto"], markers=["git_integration"])
```

Markers: `git_integration`, `claude_api_integration`, `claude_cli_integration`, `copilot_cli_integration`, `formatter_integration`, `github_integration`, `langchain_integration`, `llm_integration`, `textual_integration`.

When debugging test failures, add `"-v", "-s", "--tb=short"` to extra_args.

## Git operations

**Allowed commands via Bash tool.** These have no MCP equivalent — use Bash directly. Skills that instruct bash commands (e.g. `git commit`) must also use Bash.

```
git commit / add / rebase / push
mcp-coder check branch-status
mcp-coder check file-size --max-lines 750
mcp-coder gh-tool set-status <label>
```

**Status labels:** use `mcp-coder gh-tool set-status` to change issue workflow status — never use raw `gh issue edit` with label flags.

**Calling mcp-coder:** bare `mcp-coder` uses the tool env (stable install). To test local source changes, use `.venv\Scripts\python -m mcp_coder <args>`. See [`docs/environments/environments.md`](../docs/environments/environments.md#calling-mcp-coder-explicitly).

**Compact diff:** use `mcp__workspace__git_diff` for code review. Has compact diff built-in with exclude pattern support.

**Before every commit:** run `mcp__tools-py__run_format_code`, then stage and commit.

**Bash discipline:** no `cd` prefix, no `git -C` — commands already run in the project directory. Don't chain approved with unapproved commands. Run them separately.

**Commit messages:** standard format, clear and descriptive. No attribution footers.

## Execution directory

- `execution_dir`: where Claude subprocess runs (config discovery)
- `project_dir`: where source code lives (git ops and file modifications)

Never conflate the two. Use `--execution-dir` when workspace and project differ.

## Shared Libraries

`subprocess_runner`, `subprocess_streaming`, and `log_utils` in `src/mcp_coder/utils/` are thin shims over `mcp-coder-utils`. Always import through the local shims (`from mcp_coder.utils.<module> import ...`), not from `mcp_coder_utils` directly. Enforced by import-linter (`mcp_coder_utils_isolation` contract).

## Writing style

Be concise. If one line works, don't use three.

## Obsidian knowledge base

An Obsidian vault (`obsidian-dev-wiki`) is available via the `obsidian-wiki` MCP server.

- **Read first:** At the start of non-trivial tasks, search the vault for relevant context — repo notes, processes, known issues, prior decisions.
- **Follow processes:** When a task matches a documented process in `Processes/`, follow those steps.
- **Write back:** Update the vault when you learn something worth preserving for future sessions.

## MCP server issues

Alert immediately if MCP tools are not accessible — this blocks all work.
