# Step 3: Templates and Help Text Updates

> **Summary**: [pr_info/steps/summary.md](summary.md)
> **Covers**: Sub-tasks 4 (templates), 5 (project-dir/execution-dir help), 6 (llm-method help)
> **Depends on**: Step 2

## LLM Prompt

```
Implement Step 3 of issue #528: Update coordinator templates and CLI help text.

Read pr_info/steps/summary.md for full context, then read this step file for details.

Three sets of changes:
1. templates.py — remove "--llm-method claude" from Windows templates, add TODO on Linux
2. parsers.py — update --llm-method help text on 5 commands
3. parsers.py — improve --project-dir and --execution-dir help text

Update tests first (TDD), then the implementation. Run all three code quality checks after.
```

## WHERE

- **Source**: `src/mcp_coder/workflows/vscodeclaude/templates.py`
- **Source**: `src/mcp_coder/cli/parsers.py`
- **Tests**: `tests/workflows/vscodeclaude/test_templates.py`
- **Tests**: No new parser tests needed — help text is not typically unit-tested

## WHAT

No new functions. String constant and help text changes only.

## HOW — Templates

### `AUTOMATED_SECTION_WINDOWS`

```batch
# BEFORE:
mcp-coder prompt "{initial_command} {issue_number}" --llm-method claude --output-format session-id --mcp-config .mcp.json --timeout {timeout}

# AFTER:
mcp-coder prompt "{initial_command} {issue_number}" --output-format session-id --mcp-config .mcp.json --timeout {timeout}
```

### `DISCUSSION_SECTION_WINDOWS`

```batch
# BEFORE:
mcp-coder prompt "/discuss" --llm-method claude --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}

# AFTER:
mcp-coder prompt "/discuss" --session-id %SESSION_ID% --mcp-config .mcp.json --timeout {timeout}
```

### `AUTOMATED_SECTION_LINUX`

Add comment only:
```bash
# TODO - to be reviewed: Linux templates use raw `claude` CLI directly, not mcp-coder prompt
```

## HOW — Help Text

### `--llm-method` (5 commands: prompt, implement, create-plan, create-pr, check branch-status)

```python
# BEFORE:
help="LLM method: claude (default) or langchain"
# (or variations like "LLM method to use (default: claude)")

# AFTER:
help="LLM method override. If omitted, uses config default_provider or claude"
```

### `--project-dir` (all commands that have it)

```python
# BEFORE:
help="Project directory path (default: current directory)"

# AFTER:
help="Project directory: where source code lives (git operations, file modifications). Default: current directory"
```

### `--execution-dir` (all commands that have it)

```python
# BEFORE:
help="Working directory for Claude subprocess (default: current directory)"

# AFTER:
help="Execution directory: where Claude subprocess runs (config discovery). Default: current directory"
```

## ALGORITHM

No logic changes — string replacements only.

## DATA

No data structure changes.

## Test Cases

### `tests/workflows/vscodeclaude/test_templates.py`

1. `test_automated_section_no_hardcoded_llm_method` — assert `--llm-method` not in `AUTOMATED_SECTION_WINDOWS`
2. `test_discussion_section_no_hardcoded_llm_method` — assert `--llm-method` not in `DISCUSSION_SECTION_WINDOWS`
3. `test_linux_section_has_todo_comment` — assert `# TODO` in `AUTOMATED_SECTION_LINUX`
