---
name: implement-direct
disable-model-invocation: true
argument-hint: [issue-number]
allowed-tools: Bash(mcp-coder gh-tool *)
---

# Implement Direct

Implement a small, well-defined issue directly — no planning phase, no task tracker.

## Steps

1. **Fetch issue details**
   ```bash
   gh issue view $ARGUMENTS
   ```
   Read the issue title, description, and acceptance criteria carefully.

2. **Checkout/create issue branch**
   ```bash
   mcp-coder gh-tool checkout-issue-branch $ARGUMENTS
   ```

3. **Understand context**
   - Read relevant source files referenced in the issue
   - Understand the existing code patterns and conventions
   - Identify the minimal set of changes needed

4. **Implement changes**
   - Make the required code changes directly
   - Follow existing code patterns and conventions
   - Keep changes focused and minimal — only what the issue requires

5. **Run quality checks**
   - `mcp__tools-py__run_pylint_check` — fix all issues
   - `mcp__tools-py__run_pytest_check` (with `extra_args: ["-n", "auto"]`) — fix all failures
   - `mcp__tools-py__run_mypy_check` — fix all issues
   - `./tools/ruff_check.sh` — fix all issues

6. **Format code**
   ```bash
   ./tools/format_all.sh
   ```

7. **Suggest follow-up steps**
   - `/commit_push` — commit and push changes
   - `mcp-coder gh-tool set-status status-07:code-review` — update issue status
   - `/check_branch_status` — verify branch is clean
   - `/implementation_review` — request a review of the implementation

## Scope Guidance

This skill is designed for **small, well-defined issues** that can be implemented in a single pass. If the issue is complex or involves multiple components, recommend the full workflow instead:

1. `/create_plan` — create a detailed implementation plan
2. `/implement` — implement the plan step by step
