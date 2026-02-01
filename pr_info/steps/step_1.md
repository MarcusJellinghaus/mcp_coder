# Step 1: Refactor Test File for CI Compliance

## Objective

Split `tests/llm/providers/claude/test_claude_code_cli.py` (826 lines) into multiple files to comply with the 750-line limit.

## Prerequisites

- Step 0 completed (stream logging implementation)

## WHERE: File Paths

**Source file to split:**
- `tests/llm/providers/claude/test_claude_code_cli.py`

**New files to create:**
- `tests/llm/providers/claude/test_claude_cli_stream_parsing.py`
- `tests/llm/providers/claude/test_claude_cli_wrappers.py`

**File to keep (reduced):**
- `tests/llm/providers/claude/test_claude_code_cli.py`

## WHAT: Class Distribution

### test_claude_cli_stream_parsing.py (~230 lines)

Move these classes:
- `TestStreamJsonParsing` - Stream JSON line/file/string parsing
- `TestSanitizeBranchIdentifier` - Branch name sanitization
- `TestGetStreamLogPath` - Log path generation
- `TestCreateResponseDictFromStream` - Response dict creation from stream
- `TestStreamFileWriting` - Stream file write tests

Also move:
- `make_stream_json_output()` helper function

### test_claude_cli_wrappers.py (~220 lines)

Move these classes:
- `TestIOWrappers` - IO wrapper tests
- `TestCliLogging` - CLI logging tests

### test_claude_code_cli.py (~380 lines)

Keep these classes:
- `TestClaudeCodeCliBackwardCompatibility` - Main CLI tests
- `TestPureFunctions` - Pure function tests
- `TestEnvVarsParameter` - Environment variable tests

## HOW: Implementation Steps

1. Create `test_claude_cli_stream_parsing.py`:
   ```python
   """Tests for Claude CLI stream-json parsing functions."""
   
   # Copy imports from original file (only those needed)
   # Copy make_stream_json_output() helper
   # Copy 5 test classes related to stream parsing
   ```

2. Create `test_claude_cli_wrappers.py`:
   ```python
   """Tests for Claude CLI IO wrappers and logging."""
   
   # Copy imports from original file (only those needed)
   # Copy make_stream_json_output() helper (needed for mocking)
   # Copy 2 test classes for wrappers/logging
   ```

3. Update `test_claude_code_cli.py`:
   - Remove moved classes
   - Keep remaining 3 test classes
   - Verify imports are still correct

## ALGORITHM: Refactoring Process

```
1. Read original file content
2. Identify class boundaries by line numbers
3. Create stream_parsing file with stream-related classes
4. Create wrappers file with IO/logging classes
5. Update original file to remove moved classes
6. Run tests to verify no regressions
```

## DATA: Expected Results

| File | Line Count | Classes |
|------|------------|---------|
| test_claude_cli_stream_parsing.py | ~230 | 5 |
| test_claude_cli_wrappers.py | ~220 | 2 |
| test_claude_code_cli.py | ~380 | 3 |

## Verification

```bash
# Check file sizes
mcp-coder check file-size --max-lines 750

# Run all tests
pytest tests/llm/providers/claude/test_claude_cli*.py -v

# Verify no import errors
python -c "from tests.llm.providers.claude import test_claude_code_cli"
python -c "from tests.llm.providers.claude import test_claude_cli_stream_parsing"
python -c "from tests.llm.providers.claude import test_claude_cli_wrappers"
```

## LLM Prompt for This Step

```
Read the summary at pr_info/steps/summary.md and this step file.

Refactor tests/llm/providers/claude/test_claude_code_cli.py by splitting it into three files:

1. test_claude_cli_stream_parsing.py - Move stream parsing test classes:
   - TestStreamJsonParsing
   - TestSanitizeBranchIdentifier
   - TestGetStreamLogPath
   - TestCreateResponseDictFromStream
   - TestStreamFileWriting
   - Include make_stream_json_output() helper

2. test_claude_cli_wrappers.py - Move IO wrapper test classes:
   - TestIOWrappers
   - TestCliLogging
   - Include make_stream_json_output() helper

3. test_claude_code_cli.py - Keep remaining classes:
   - TestClaudeCodeCliBackwardCompatibility
   - TestPureFunctions
   - TestEnvVarsParameter

After splitting:
- Run mcp__code-checker__run_pytest_check to verify tests pass
- Run mcp-coder check file-size to verify all files are under 750 lines
```
