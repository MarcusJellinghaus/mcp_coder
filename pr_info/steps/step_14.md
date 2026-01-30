# Step 14: Add `--output-format session-id` to Prompt Command

## LLM Prompt

```
Implement Step 14 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Add session-id output format option to the prompt command.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/prompt.py` | Modify - add session-id output format |
| `src/mcp_coder/cli/main.py` | Modify - update output-format help text |
| `tests/cli/commands/test_prompt.py` | Add - tests for session-id format |

## WHAT

### prompt.py - Add Session ID Output Format

```python
def execute_prompt(args: argparse.Namespace) -> int:
    """Execute prompt command to ask Claude a question.
    
    Enhanced to support --output-format session-id which returns
    only the session_id string for easy shell script capture.
    """
    # ... existing code ...
    
    # Handle output_format
    output_format = getattr(args, "output_format", "text")
    
    if output_format == "session-id":
        # Return only session_id for shell script capture
        # Uses prompt_llm() to get full response with session_id
        from ...llm.interface import prompt_llm
        
        provider, method = parse_llm_method_from_args(llm_method)
        response_dict = prompt_llm(
            args.prompt,
            provider=provider,
            method=method,
            timeout=timeout,
            session_id=resume_session_id,
            env_vars=env_vars,
            project_dir=str(project_dir),
            execution_dir=str(execution_dir),
            mcp_config=mcp_config,
        )
        
        session_id = response_dict.get("session_id", "")
        if not session_id:
            print("Error: No session_id in response", file=sys.stderr)
            return 1
        
        print(session_id)
        return 0
    
    # ... rest of existing code for text/json formats ...
```

### main.py - Update Help Text

```python
# In create_prompt_parser()
parser.add_argument(
    "--output-format",
    dest="output_format",
    metavar="FORMAT",
    default="text",
    help="Output format: text (default), json (includes session_id), or session-id (only session_id)",
)
```

## HOW

### Integration Points

1. Uses existing `prompt_llm()` function which returns `LLMResponseDict` with session_id
2. New format is a simple addition to existing output_format handling
3. Error handling: return exit code 1 if no session_id available

### Shell Script Usage

Windows (.bat):
```batch
for /f %%i in ('mcp-coder prompt "/issue_analyse 123" --output-format session-id --mcp-config .mcp.json --timeout 300') do set SESSION_ID=%%i
```

Linux (.sh):
```bash
SESSION_ID=$(mcp-coder prompt "/issue_analyse 123" --output-format session-id --mcp-config .mcp.json --timeout 300)
```

## ALGORITHM

```
1. Parse output_format from args
2. If output_format == "session-id":
   a. Call prompt_llm() to get full response
   b. Extract session_id from response
   c. If no session_id: print error to stderr, return 1
   d. Print session_id to stdout, return 0
3. Else: continue with existing text/json handling
```

## DATA

### Return Values

| output_format | stdout | stderr | exit code |
|---------------|--------|--------|-----------|
| text | Response text | (errors) | 0 or 1 |
| json | Full JSON | (errors) | 0 or 1 |
| session-id | Session ID only | (errors) | 0 or 1 |

### Test Coverage

```python
# test_prompt.py

class TestSessionIdOutputFormat:
    """Test --output-format session-id functionality."""
    
    def test_session_id_format_returns_only_session_id(self, monkeypatch):
        """With --output-format session-id, prints only the session_id."""
        mock_response = {
            "text": "Response text here",
            "session_id": "abc123-session-id",
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.prompt.prompt_llm",
            lambda *args, **kwargs: mock_response,
        )
        
        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            timeout=30,
            llm_method="claude_code_cli",
            session_id=None,
            # ... other required args
        )
        
        with patch("builtins.print") as mock_print:
            result = execute_prompt(args)
        
        assert result == 0
        mock_print.assert_called_once_with("abc123-session-id")
    
    def test_session_id_format_error_when_no_session_id(self, monkeypatch):
        """Returns error when response has no session_id."""
        mock_response = {
            "text": "Response text",
            "session_id": None,  # No session_id
            # ... other fields
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.prompt.prompt_llm",
            lambda *args, **kwargs: mock_response,
        )
        
        args = argparse.Namespace(
            prompt="test prompt",
            output_format="session-id",
            # ... other args
        )
        
        result = execute_prompt(args)
        
        assert result == 1  # Error exit code
    
    def test_session_id_format_with_resume(self, monkeypatch):
        """Session ID format works when resuming existing session."""
        mock_response = {
            "text": "Continued response",
            "session_id": "existing-session-456",
            # ... other fields
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.prompt.prompt_llm",
            lambda *args, **kwargs: mock_response,
        )
        
        args = argparse.Namespace(
            prompt="/discuss",
            output_format="session-id",
            session_id="existing-session-456",
            # ... other args
        )
        
        with patch("builtins.print") as mock_print:
            result = execute_prompt(args)
        
        assert result == 0
        mock_print.assert_called_once_with("existing-session-456")
```

## Verification

```bash
# Run prompt tests
pytest tests/cli/commands/test_prompt.py::TestSessionIdOutputFormat -v

# Type check
mypy src/mcp_coder/cli/commands/prompt.py

# Manual test
mcp-coder prompt "What is 1+1?" --output-format session-id
```
