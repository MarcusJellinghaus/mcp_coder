# Step 6: CLI Wiring

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Steps 1-5 (all core + services)

## Goal
Register the `mcp-coder icoder` CLI command with standard flags (`--llm-method`, `--mcp-config`, `--project-dir`, `--execution-dir`). Follow the existing CLI patterns exactly.

## WHERE — Files

### New files
- `src/mcp_coder/cli/commands/icoder.py`
- `tests/icoder/test_cli_icoder.py`

### Modified files
- `src/mcp_coder/cli/parsers.py` — add `add_icoder_parser()`
- `src/mcp_coder/cli/main.py` — add import + route

## WHAT — Main Functions and Signatures

### `cli/parsers.py` — new function

```python
def add_icoder_parser(subparsers: Any) -> None:
    """Add the icoder command parser."""
    # Flags: --llm-method, --mcp-config, --project-dir, --execution-dir
```

### `cli/main.py` — additions

```python
# Import
from .commands.icoder import execute_icoder

# In create_parser():
add_icoder_parser(subparsers)

# In main() routing:
elif args.command == "icoder":
    return execute_icoder(args)
```

### `cli/commands/icoder.py`

```python
def execute_icoder(args: argparse.Namespace) -> int:
    """Execute the iCoder interactive TUI.
    
    Resolves CLI parameters, creates core components, launches Textual app.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
```

## HOW — Integration Points

- Parser follows exact same pattern as `add_implement_parser()` — same flags, same help strings
- `execute_icoder()` follows same pattern as `execute_prompt()`:
  1. `resolve_execution_dir(args.execution_dir)`
  2. `prepare_llm_environment(project_dir)`
  3. `resolve_llm_method(args.llm_method)` → `parse_llm_method_from_args()`
  4. `resolve_mcp_config_path(args.mcp_config, args.project_dir)`
  5. Find latest session via `find_latest_session(provider=provider)`
  6. Create `RealLLMService(provider, session_id, execution_dir, mcp_config, env_vars)`
  7. Create `EventLog(logs_dir=project_dir / "logs")`
  8. Create `AppCore(llm_service, event_log)`
  9. Launch `ICoderApp(app_core).run()` ← **import deferred to step 7; step 6 just validates wiring**
- Import of `add_icoder_parser` added to the imports in `main.py`

## ALGORITHM — Core Logic

```
execute_icoder(args):
    execution_dir = resolve_execution_dir(args.execution_dir)
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    env_vars = prepare_llm_environment(project_dir)
    provider = parse_llm_method_from_args(resolve_llm_method(args.llm_method)[0])
    mcp_config = resolve_mcp_config_path(args.mcp_config, args.project_dir)
    session_id = find_latest_session_id(provider)  # helper that extracts ID
    llm_service = RealLLMService(provider, session_id, str(execution_dir), mcp_config, env_vars)
    event_log = EventLog(logs_dir=project_dir / "logs")
    app_core = AppCore(llm_service, event_log)
    ICoderApp(app_core).run()  # Textual app blocks until exit
    event_log.close()
    return 0
```

## DATA — Return Values

- `execute_icoder()` returns `int` (exit code: 0 success, 1 error)
- `add_icoder_parser()` returns `None` (mutates subparsers)

## Tests — `tests/icoder/test_cli_icoder.py`

```python
# Test parser is registered (icoder appears in subcommands)
def test_icoder_parser_registered():
    parser = create_parser()
    # Parse "icoder" command — should not raise
    args = parser.parse_args(["icoder"])
    assert args.command == "icoder"

# Test parser accepts --llm-method flag
def test_icoder_llm_method_flag():
    parser = create_parser()
    args = parser.parse_args(["icoder", "--llm-method", "langchain"])
    assert args.llm_method == "langchain"

# Test parser accepts --project-dir flag
def test_icoder_project_dir_flag():
    parser = create_parser()
    args = parser.parse_args(["icoder", "--project-dir", "/tmp/test"])
    assert args.project_dir == "/tmp/test"

# Test parser accepts --mcp-config flag
def test_icoder_mcp_config_flag():
    parser = create_parser()
    args = parser.parse_args(["icoder", "--mcp-config", "/tmp/.mcp.json"])
    assert args.mcp_config == "/tmp/.mcp.json"

# Test parser accepts --execution-dir flag
def test_icoder_execution_dir_flag():
    parser = create_parser()
    args = parser.parse_args(["icoder", "--execution-dir", "/tmp/exec"])
    assert args.execution_dir == "/tmp/exec"

# Test parser default values
def test_icoder_default_values():
    parser = create_parser()
    args = parser.parse_args(["icoder"])
    assert args.llm_method is None
    assert args.project_dir is None
    assert args.mcp_config is None
    assert args.execution_dir is None

# Test execute_icoder is importable and callable
def test_execute_icoder_importable():
    from mcp_coder.cli.commands.icoder import execute_icoder
    assert callable(execute_icoder)

# Test main.py routes to icoder (mock execute_icoder)
def test_main_routes_icoder(monkeypatch):
    """Verify main() dispatches 'icoder' to execute_icoder."""
    called = {}
    def mock_execute(args):
        called["args"] = args
        return 0
    monkeypatch.setattr("mcp_coder.cli.main.execute_icoder", mock_execute)
    from mcp_coder.cli.main import main
    monkeypatch.setattr("sys.argv", ["mcp-coder", "icoder"])
    result = main()
    assert result == 0
    assert called["args"].command == "icoder"
```

## LLM Prompt

```
You are implementing Step 6 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Add add_icoder_parser() to src/mcp_coder/cli/parsers.py
   - Flags: --llm-method, --mcp-config, --project-dir, --execution-dir
   - Follow exact same pattern as add_implement_parser()
2. Wire icoder command in src/mcp_coder/cli/main.py
   - Import execute_icoder + add_icoder_parser
   - Add add_icoder_parser(subparsers) in create_parser()
   - Add routing: elif args.command == "icoder": return execute_icoder(args)
3. Create src/mcp_coder/cli/commands/icoder.py with execute_icoder()
   - Follow same parameter resolution pattern as execute_prompt()
   - For now, the Textual app import can be guarded (UI built in step 7)
   - Function should resolve all params and create AppCore components
4. Write tests in tests/icoder/test_cli_icoder.py
5. Run pylint, mypy, pytest to verify all checks pass

Key details:
- Parser follows EXACT same pattern as add_implement_parser()
- execute_icoder() follows same resolution chain as execute_prompt()
- Session auto-resume: find_latest_session(provider=provider) on launch
- The actual Textual app launch will be added in step 7

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
