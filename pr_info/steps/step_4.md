# Step 4: Copilot JSONL parser + tool permission converter

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 4 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Create the JSONL parsing functions and the settings.local.json → Copilot tool flags converter in `src/mcp_coder/llm/providers/copilot/copilot_cli.py`. This step covers only the pure parsing/conversion functions — the command builder and `ask_copilot_cli()` come in Step 5. Follow TDD.

## WHERE

### New files
- `src/mcp_coder/llm/providers/copilot/copilot_cli.py` (partial — parser + converter only)
- `tests/llm/providers/copilot/conftest.py`
- `tests/llm/providers/copilot/test_copilot_cli.py` (partial — parser + converter tests)

## WHAT

### JSONL parsing functions in `copilot_cli.py`

```python
def parse_copilot_jsonl_line(line: str) -> dict[str, Any] | None:
    """Parse a single JSONL line from Copilot output.

    Returns parsed dict or None if line is empty/invalid.
    """

def parse_copilot_jsonl_output(lines: list[str]) -> ParsedCopilotResponse:
    """Parse complete Copilot JSONL output into structured response.

    Extracts:
    - text from assistant.message content blocks
    - session_id from result message's sessionId field
    - usage: outputTokens → output_tokens mapping
    - Copilot-specific fields into raw_response
    """
```

### `ParsedCopilotResponse` TypedDict

```python
class ParsedCopilotResponse(TypedDict):
    text: str
    session_id: str | None
    messages: list[dict[str, Any]]   # all parsed JSONL messages
    usage: dict[str, object]         # mapped usage info
    raw_result: dict[str, Any] | None  # the result JSONL message
```

### Tool permission converter

```python
class CopilotToolFlags(TypedDict):
    available_tools: list[str]   # flat hyphen format for --available-tools
    allow_tools: list[str]       # parentheses format for --allow-tool

def convert_settings_to_copilot_tools(
    allow_entries: list[str],
) -> CopilotToolFlags:
    """Convert .claude/settings.local.json permission entries to Copilot CLI flags.

    Mapping rules:
    - mcp__<server>__<tool> → <server>-<tool> (for --available-tools)
    - Bash(<cmd>:<pattern>) → shell(<cmd>:<pattern>) (for --allow-tool)
    - Skill(...), WebFetch(...) → skipped with warning

    Args:
        allow_entries: List of permission strings from settings.local.json

    Returns:
        CopilotToolFlags with two lists of flag values.
    """
```

## HOW

- `copilot_cli.py` imports: `json`, `logging`, `typing`, `re`
- No project dependencies needed for pure parsing/conversion functions.
- Converter uses `logging.warning()` for unmappable entries.

## ALGORITHM

### JSONL parser
```
1. For each line: json.loads(), skip empty/invalid
2. If type == "assistant.message": extract text from content[].text blocks, collect toolRequests
3. If type == "tool.execution_complete": store tool results
4. If type == "result": extract sessionId, usage (outputTokens → output_tokens), store raw
5. Skip all other types (ephemeral)
6. Return ParsedCopilotResponse
```

### Tool converter
```
1. For each entry in allow_entries:
2.   If starts with "mcp__": split on "mcp__" prefix + "__" separator → server-tool format → available_tools
3.   If starts with "Bash(": replace "Bash(" with "shell(" → allow_tools
4.   If starts with "Skill(" or "WebFetch(": log warning, skip
5.   Else: log warning (unknown format), skip
6. Return CopilotToolFlags
```

## DATA

### JSONL message types handled

| Copilot JSONL type | Action |
|---|---|
| `assistant.message` | Extract text + toolRequests |
| `tool.execution_complete` | Store tool result |
| `result` | Extract sessionId, usage, exitCode |
| Everything else | Skip (ephemeral) |

### Tool converter examples

| Input | Output bucket | Output value |
|---|---|---|
| `mcp__workspace__read_file` | `available_tools` | `workspace-read_file` |
| `mcp__tools-py__run_pytest_check` | `available_tools` | `tools-py-run_pytest_check` |
| `mcp__obsidian-wiki__read-note` | `available_tools` | `obsidian-wiki-read-note` |
| `Bash(git diff:*)` | `allow_tools` | `shell(git diff:*)` |
| `Skill(commit_push)` | (skipped) | warning logged |
| `WebFetch(domain:*)` | (skipped) | warning logged |

## Tests

### `tests/llm/providers/copilot/conftest.py`
Factory fixture `make_copilot_jsonl_output` that creates valid canned JSONL strings with configurable text, session_id, and usage.

### `tests/llm/providers/copilot/test_copilot_cli.py`

#### Parser tests
- `test_parse_jsonl_line_valid` — valid JSON line returns dict
- `test_parse_jsonl_line_empty` — empty string returns None
- `test_parse_jsonl_line_invalid_json` — bad JSON returns None
- `test_parse_output_extracts_text` — text from assistant.message
- `test_parse_output_extracts_session_id` — sessionId from result
- `test_parse_output_maps_usage` — outputTokens → output_tokens
- `test_parse_output_skips_ephemeral_types` — session.info, assistant.reasoning etc. don't appear in text
- `test_parse_output_handles_tool_requests` — toolRequests in assistant.message
- `test_parse_output_empty_input` — empty list returns empty response

#### Tool converter tests
- `test_convert_mcp_tool_basic` — `mcp__workspace__read_file` → `workspace-read_file`
- `test_convert_mcp_tool_hyphenated_server` — `mcp__tools-py__run_pytest_check` → `tools-py-run_pytest_check`
- `test_convert_mcp_tool_hyphenated_server_name` — `mcp__obsidian-wiki__read-note` → `obsidian-wiki-read-note`
- `test_convert_bash_to_shell` — `Bash(git diff:*)` → `shell(git diff:*)`
- `test_convert_skill_skipped_with_warning` — `Skill(commit_push)` skipped, warning logged
- `test_convert_webfetch_skipped_with_warning` — `WebFetch(domain:*)` skipped, warning logged
- `test_convert_mixed_entries` — real-world mix from settings.local.json
- `test_convert_empty_list` — returns empty lists
