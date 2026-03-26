# Step 6: CLI Changes — New Output Formats, Remove --verbosity, Wire Streaming

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 6: update CLI to add `ndjson` and `json-raw` output formats, remove `--verbosity`, and wire streaming into `execute_prompt()`. Follow TDD — write/update tests first, then implement. Run all three code quality checks (pylint, pytest, mypy) after changes. Commit as `feat(cli): add streaming output formats, remove --verbosity`.

## WHERE

- **Modify**: `src/mcp_coder/cli/parsers.py`
- **Modify**: `src/mcp_coder/cli/commands/prompt.py`
- **Modify**: `tests/cli/commands/test_prompt.py`
- **Create**: `tests/cli/commands/test_prompt_streaming.py` (new — streaming-specific tests)

## WHAT

### Changes in `parsers.py`:

```python
# REMOVE the --verbosity argument entirely

# UPDATE --output-format choices:
prompt_parser.add_argument(
    "--output-format",
    choices=["text", "ndjson", "json-raw", "json", "session-id"],
    default="text",
    metavar="FORMAT",
    help="Output format: text (streaming default), ndjson (normalized streaming), "
         "json-raw (raw streaming), json (complete JSON), session-id (ID only)",
)
```

### Changes in `prompt.py` (`execute_prompt`):

```python
def execute_prompt(args: argparse.Namespace) -> int:
    # ... existing setup (env, provider, session resolution) unchanged ...

    output_format = getattr(args, "output_format", "text")

    if output_format in ("text", "ndjson", "json-raw"):
        # STREAMING PATH
        return _execute_prompt_streaming(args, output_format, ...)
    elif output_format == "session-id":
        # ... existing session-id logic unchanged ...
    elif output_format == "json":
        # ... existing json logic unchanged ...


def _execute_prompt_streaming(
    args: argparse.Namespace,
    output_format: str,
    provider: str,
    resume_session_id: str | None,
    env_vars: dict[str, str] | None,
    execution_dir: str,
    mcp_config: str | None,
    branch_name: str | None,
) -> int:
    """Execute prompt with streaming output.

    Streams events to stdout via print_stream_event(), assembles
    LLMResponseDict via ResponseAssembler, handles store-response.

    Returns:
        Exit code (0 for success, 1 for error)
    """
```

## HOW

- Import `prompt_llm_stream` from `...llm.interface`
- Import `ResponseAssembler`, `StreamEvent` from `...llm.types`
- Import `print_stream_event` from `...llm.formatting.formatters`
- Remove imports: `format_raw_response`, `format_verbose_response`, `format_text_response`
- Remove all `verbosity` references from `execute_prompt()`
- The streaming path uses the simple dispatch loop pattern:

```python
assembler = ResponseAssembler(provider=provider)
for event in prompt_llm_stream(...):
    assembler.add(event)
    print_stream_event(event, output_format)
response = assembler.result()
```

- After streaming completes: handle `--store-response` and MLflow logging using the assembled `LLMResponseDict`

## ALGORITHM

```
def _execute_prompt_streaming(args, output_format, provider, session_id, env_vars, execution_dir, mcp_config, branch_name):
    assembler = ResponseAssembler(provider)
    try:
        for event in prompt_llm_stream(args.prompt, provider, session_id, timeout, env_vars, execution_dir, mcp_config, branch_name):
            assembler.add(event)
            print_stream_event(event, output_format)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    response = assembler.result()
    if getattr(args, "store_response", False):
        store_session(response, args.prompt, branch_name=branch_name)
    return 0
```

## DATA

### CLI argument changes

| Before | After |
|--------|-------|
| `--output-format text\|json\|session-id` | `--output-format text\|ndjson\|json-raw\|json\|session-id` |
| `--verbosity just-text\|verbose\|raw` | (removed) |

### Output behavior by format

| Format | Streaming | Behavior |
|--------|-----------|----------|
| `text` | Yes | Tokens printed as they arrive, tool calls as bordered sections |
| `ndjson` | Yes | Normalized NDJSON lines (Claude schema) |
| `json-raw` | Yes | Raw provider events as NDJSON |
| `json` | No | Single JSON blob after completion (unchanged) |
| `session-id` | No | Session ID string only (unchanged) |

## TEST CASES

### Update `tests/cli/commands/test_prompt.py`:
1. Remove/update all tests that reference `verbosity` attribute
2. Update `argparse.Namespace` fixtures to not include `verbosity`
3. Keep all existing `session-id` and `json` format tests unchanged

### New `tests/cli/commands/test_prompt_streaming.py`:
1. `test_text_format_streams_events` — mock prompt_llm_stream, verify print_stream_event called for each event
2. `test_ndjson_format_streams_events` — mock prompt_llm_stream, verify ndjson output
3. `test_json_raw_format_streams_events` — mock prompt_llm_stream, verify raw output
4. `test_streaming_assembles_response` — verify ResponseAssembler.result() called after stream
5. `test_streaming_store_response` — verify store_session called with assembled response when --store-response
6. `test_streaming_error_returns_1` — mock stream raising exception, verify exit code 1
7. `test_json_format_unchanged` — verify json format still uses blocking prompt_llm()
8. `test_session_id_format_unchanged` — verify session-id format still uses blocking prompt_llm()
9. `test_default_format_is_text` — verify text is default output format

### Verbosity removal checklist:
- `parsers.py`: remove `--verbosity` argument
- `prompt.py`: remove `verbosity` getattr and all verbosity-based branching
- `prompt.py`: remove imports of `format_text_response`, `format_verbose_response`, `format_raw_response`
- `test_prompt.py`: remove `verbosity` from all argparse.Namespace objects
- Note: keep `formatters.py` functions for now (they may still be used elsewhere) — remove in a follow-up if truly unused
