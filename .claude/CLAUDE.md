## About this repo

`mcp-coder` is a CLI and workflow orchestrator for LLM sessions, using Claude Code or langchain as backend.

## MCP Tools — mandatory

**Do NOT use native Claude Code file tools** (`Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`) for any operation that has an MCP equivalent. Always use the `mcp__mcp-workspace__*` tools instead. This applies to all file reading, writing, editing, searching, listing, and git operations. If no MCP equivalent exists, use Bash. Check the tool mapping table below first.

**Justify Bash.** Before a Bash command or script, say in chat, on two lines:

- *What it does* — one sentence.
- *Why MCP doesn't* — which tool you'd have used, and what stops it.

If you can't name the gap, use the MCP tool. Exempt: the approved git/gh commands under Git operations.

**No session scratchpad.** MCP tools can't write outside the project. Temporary files go in `.scratch/`.


### Tool mapping

| Task | MCP tool |
|------|----------|
| Read file | `mcp__mcp-workspace__read_file` |
| Edit file | `mcp__mcp-workspace__edit_file` |
| Write file | `mcp__mcp-workspace__save_file` |
| Append to file | `mcp__mcp-workspace__append_file` |
| Delete file | `mcp__mcp-workspace__delete_this_file` |
| Move file | `mcp__mcp-workspace__move_file` |
| List directory | `mcp__mcp-workspace__list_directory` |
| Search files | `mcp__mcp-workspace__search_files` |
| Read reference project | `mcp__mcp-workspace__read_reference_file` |
| List reference dir | `mcp__mcp-workspace__list_reference_directory` |
| Get reference projects | `mcp__mcp-workspace__get_reference_projects` |
| Search reference files | `mcp__mcp-workspace__search_reference_files` |
| Get base branch | `mcp__mcp-workspace__get_base_branch` |
| Check file size | `mcp__mcp-workspace__check_file_size` |
| Check branch status | `mcp__mcp-workspace__check_branch_status` |
| Run pytest | `mcp__mcp-tools-py__run_pytest_check` |
| Run pylint | `mcp__mcp-tools-py__run_pylint_check` |
| Run mypy | `mcp__mcp-tools-py__run_mypy_check` |
| Run vulture | `mcp__mcp-tools-py__run_vulture_check` |
| Run lint-imports | `mcp__mcp-tools-py__run_lint_imports_check` |
| Run ruff check | `mcp__mcp-tools-py__run_ruff_check` |
| Run ruff fix | `mcp__mcp-tools-py__run_ruff_fix` |
| Run bandit | `mcp__mcp-tools-py__run_bandit_check` |
| Run tach | `mcp__mcp-tools-py__run_tach_check` |
| Format code (black+isort) | `mcp__mcp-tools-py__run_format_code` |
| Check a Python semantic before claiming it | scratch probe — see [Scratch probes](#scratch-probes) |
| Get library source of installed deps (never `python -c "__file__"` + cat site-packages) | `mcp__mcp-tools-py__get_library_source` |
| Refactoring | `mcp__mcp-tools-py__move_symbol`, `move_module`, `rename_symbol`, `list_symbols`, `find_references` |
| Git read-only (status, diff, log, show, fetch, ls_tree, ls_files, ls_remote, rev_parse, branch list) | `mcp__mcp-workspace__git` |
| `gh issue view` | `mcp__mcp-workspace__github_issue_view` |
| `gh issue list` | `mcp__mcp-workspace__github_issue_list` |
| `gh pr view` | `mcp__mcp-workspace__github_pr_view` |
| `gh search` | `mcp__mcp-workspace__github_search` |

Sibling repos are readable in full via the reference tools and `git` with `reference_name` (`get_reference_projects` lists them). Check there before asking about another repo.

## Code quality checks

After making code changes, run:

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check
mcp__mcp-tools-py__run_mypy_check
```

All checks must pass before proceeding.

**Ruff:** use `mcp__mcp-tools-py__run_ruff_check`. Do not call `ruff` directly.

**Pytest:** always use `extra_args: ["-n", "auto"]` for parallel execution.

```python
# Fast unit tests (recommended)
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])

# Specific integration tests
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto"], markers=["git_integration"])
```

Markers: `git_integration`, `claude_api_integration`, `claude_cli_integration`, `copilot_cli_integration`, `formatter_integration`, `github_integration`, `jenkins_integration`, `langchain_integration`, `llm_integration`, `textual_integration`.

When debugging test failures, add `"-v", "-s", "--tb=short"` to extra_args.

## Scratch probes

Don't assert Python behaviour you haven't run. Probe it:

```python
mcp__mcp-workspace__save_file(".scratch/test_probe.py", ...)
mcp__mcp-tools-py__run_pytest_check(extra_args=["-p", "no:cacheprovider", ".scratch/test_probe.py"])
```

A path argument scopes the run, so a probe costs seconds. Delete when done — `delete_directory(".scratch", recursive=True)`; CI blocks any PR carrying one. `.scratch/` is not gitignored: the MCP file tools refuse ignored paths.

Never use `python -c` via Bash. If you reason instead of running, label the conclusion analytical.

## Git operations

**Allowed commands via Bash tool.** These have no MCP equivalent — use Bash directly. Skills that instruct bash commands (e.g. `git commit`) must also use Bash.

```
git commit / add / rebase / push / checkout -b / branch
gh issue create / edit / comment (labels only via set-status)
gh issue view (cross-repo only — otherwise use the MCP tool)
gh pr create
mcp-coder gh-tool set-status <label>
```

**Status labels:** use `mcp-coder gh-tool set-status` to change issue workflow status — never use raw `gh issue edit` with label flags.

**Slash-prefixed `gh` arguments:** prefix with `MSYS_NO_PATHCONV=1` — Git Bash rewrites a leading `/` into a Windows path.

**Privileged agents:** `commit-pusher`, `issue-updater` and `issue-approver` run with `bypassPermissions`, so they skip the prompts these commands normally trigger. That is an ergonomics device, not access control — any session can launch them, and `Bash` is unrestricted inside them. Rationale and limits: `docs/repository-setup/agent-permissions.md` in the mcp-coder repository.

**Calling mcp-coder:** bare `mcp-coder` uses the tool env (stable install). To test local source changes, use `.venv\Scripts\python -m mcp_coder <args>`. See [`docs/environments/environments.md`](../docs/environments/environments.md#calling-mcp-coder-explicitly).

**Compact diff:** use `mcp__mcp-workspace__git` for code review. Has compact diff built-in with exclude pattern support.

**Before every commit:** run `mcp__mcp-tools-py__run_format_code`, then stage and commit.

**Bash discipline:** no `cd` prefix, no `git -C` — commands already run in the project directory. Don't chain approved with unapproved commands. Run them separately.

**Commit messages:** standard format. See Writing style for length. No attribution footers.

**Multi-line commit messages:** use a POSIX heredoc — `git commit -F - <<'EOF' … EOF`. PowerShell here-strings (`@'...'@`) work only in the PowerShell tool; in Bash they silently leave a literal `@` in the subject line.

## Shared Libraries

This repo uses `mcp-coder-utils` for subprocess execution, logging, and redaction. Three shim modules in `src/mcp_coder/utils/` re-export the upstream API:

| Shim module | Upstream module | Key imports |
|-------------|-----------------|-------------|
| `mcp_coder.utils.subprocess_runner` | `mcp_coder_utils.subprocess_runner` | `execute_command`, `execute_subprocess`, `CommandResult`, `CommandOptions`, `launch_process`, `prepare_env` |
| `mcp_coder.utils.subprocess_streaming` | `mcp_coder_utils.subprocess_streaming` | `stream_subprocess`, `StreamResult` |
| `mcp_coder.utils.log_utils` | `mcp_coder_utils.log_utils` + `redaction` | `setup_logging`, `log_function_call`, `OUTPUT`, `REDACTED_VALUE`, `RedactableDict` |

**Rules:**
- Always import through the local shims (`from mcp_coder.utils.<module> import ...`), never from `mcp_coder_utils` directly. Enforced by import-linter (`mcp_coder_utils_isolation` contract).
- Do not reimplement utilities that exist in mcp-coder-utils. When in doubt, check the source first.
- Full source: reference project `mcp-coder-utils` — use `mcp__mcp-workspace__read_reference_file`.

## Writing style

Be concise. Shorter is better — chat, commits, PRs, docs, comments alike.

Say it once. Never restate what the reader can already see: the diff, the code, the issue, or my own earlier message. Cut it; don't rephrase it.

If a sentence isn't load-bearing, delete it.

Readable beats short. Cut what I don't need; don't compress what stays — complete sentences, no arrow chains or invented abbreviations. Lead with the outcome.

## Asking questions

Never use the AskUserQuestion tool. Ask questions as plain text in the chat.

## Obsidian knowledge base

Shared knowledge base across my repos (`obsidian-dev-wiki`), via the `obsidian-wiki` MCP server.

**Read at the start of non-trivial work:** `Home.md` (index), the `Repos/<current repo>.md` note, and any `Processes/` note matching the task. If a process note covers the task, follow it rather than improvising.

**Write only what passes all three tests:**

- *durable* — still true in 6 months (not status, versions, or task state)
- *general* — applies beyond the one issue that produced it
- *homeless* — no better place already exists

Existing homes, check before writing: code and docstrings; the repo's `docs/`; CLAUDE.md for how-I-work rules; the GitHub issue for a single defect's root cause; git history for what changed when.

**Always write to `Field Notes/`**, for Marcus to promote. Only edit `Repos/`, `Processes/`, or `Plans/` when Marcus explicitly asks for it. If an existing note already covers the topic, name it in the Field Note (`Promote into [[Note Name]]`) instead of editing that note. Follow `Conventions.md` for frontmatter and naming.

## MCP server issues

Alert immediately if MCP tools are not accessible — this blocks all work.
