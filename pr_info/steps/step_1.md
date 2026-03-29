# Step 1: Improve `--continue-session` no-session message

## LLM Prompt

> Refer to `pr_info/steps/summary.md` for context.
> Implement Step 1: Add a test that verifies the improved user-facing message when `--continue-session` finds no previous sessions, then update the message string. Run all code quality checks and commit.

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/test_prompt_continue_session_message.py` | **Create** — new test file |
| `src/mcp_coder/cli/commands/prompt.py` | **Modify** — line 99 |

## WHAT

### Test (`test_prompt_continue_session_message.py`)

```python
def test_continue_session_no_previous_sessions_message(capsys):
    """Verify the message includes --store-response guidance."""
```

- Mocks `find_latest_session` to return `None`
- Mocks `prompt_llm_stream` to yield a minimal event
- Calls `execute_prompt` with `continue_session=True`
- Asserts captured stdout contains `"Save conversations with --store-response"`

### Production change (`prompt.py`)

No new functions. Single string edit:

```python
# Before
print("No previous response files found, starting new conversation")

# After
print("No previous response files found, starting new conversation. Save conversations with --store-response")
```

## HOW

- Test uses `unittest.mock.patch` to mock `find_latest_session` and `prompt_llm_stream`
- Test creates a minimal `argparse.Namespace` matching `execute_prompt`'s expected attributes

## ALGORITHM

```
1. find_latest_session returns None  (mocked)
2. execute_prompt prints improved message
3. execution continues to prompt_llm_stream  (mocked to return immediately)
4. test captures stdout via capsys
5. assert "Save conversations with --store-response" in captured output
```

## DATA

- **Input**: `argparse.Namespace(continue_session=True, prompt="test", ...)`
- **Output**: stdout contains the improved message string
- **Return**: `execute_prompt` returns `0` (success)

## Commit

```
fix(cli): improve --continue-session message when no sessions found (#625)
```
