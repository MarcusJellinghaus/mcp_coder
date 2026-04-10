# Step 1: `--no-format-tools` CLI Flag + Plumbing

## Context
See [summary.md](summary.md) for overall design. This step adds the `--no-format-tools` flag and threads `format_tools: bool` through the entire call chain: CLI parser → `execute_icoder()` → `ICoderApp` → `StreamEventRenderer`. No formatting logic changes yet — just the wiring.

## LLM Prompt
> Implement Step 1 of issue #763 (see `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`).
> Add the `--no-format-tools` CLI flag and thread `format_tools: bool` from CLI through to `StreamEventRenderer`.
> Write tests first (TDD), then implement. Run all three quality checks after changes.

## Part A: Tests

### WHERE
- `tests/icoder/test_cli_icoder.py`
- `tests/llm/formatting/test_stream_renderer.py`

### WHAT — New test functions

**`tests/icoder/test_cli_icoder.py`:**
```python
def test_icoder_no_format_tools_flag() -> None:
    """Test parser accepts --no-format-tools flag."""

def test_icoder_no_format_tools_default() -> None:
    """Test --no-format-tools defaults to False (formatting on)."""

def test_execute_icoder_passes_format_tools_to_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify format_tools=False is passed to ICoderApp when --no-format-tools is set."""
```

**Existing test update required:**
- `test_execute_icoder_creates_registry_with_skills`: Update monkeypatched `capturing_init` to accept `**kwargs`, since `execute_icoder()` will now pass `format_tools=` keyword argument.

**`tests/llm/formatting/test_stream_renderer.py`:**
```python
def test_renderer_format_tools_default_true() -> None:
    """StreamEventRenderer defaults to format_tools=True."""

def test_renderer_format_tools_false() -> None:
    """StreamEventRenderer accepts format_tools=False."""
```

### DATA
- Parser: `args.no_format_tools` is `True` when flag present, absent/`False` by default
- `format_tools = not args.no_format_tools` (invert: flag disables formatting)

## Part B: Implementation

### WHERE
1. `src/mcp_coder/cli/parsers.py` — `add_icoder_parser()`
2. `src/mcp_coder/cli/commands/icoder.py` — `execute_icoder()`
3. `src/mcp_coder/icoder/ui/app.py` — `ICoderApp.__init__()`
4. `src/mcp_coder/llm/formatting/stream_renderer.py` — `StreamEventRenderer.__init__()`

### WHAT — Signatures

```python
# parsers.py — add to add_icoder_parser():
icoder_parser.add_argument(
    "--no-format-tools",
    action="store_true",
    help="Disable tool output formatting (show raw output)",
)

# stream_renderer.py
class StreamEventRenderer:
    def __init__(self, *, format_tools: bool = True) -> None:
        self._format_tools = format_tools

# app.py
class ICoderApp(App[None]):
    def __init__(self, app_core: AppCore, *, format_tools: bool = True, **kwargs: Any) -> None:
        ...
        self._format_tools = format_tools
        self._renderer = StreamEventRenderer(format_tools=format_tools)
```

### HOW — Integration

```python
# icoder.py — in execute_icoder():
format_tools = not getattr(args, "no_format_tools", False)
# ... later:
ICoderApp(app_core, format_tools=format_tools).run()
```

### ALGORITHM
```
1. Parser adds --no-format-tools (store_true)
2. execute_icoder reads flag, inverts to format_tools bool
3. ICoderApp stores format_tools, passes to StreamEventRenderer
4. StreamEventRenderer stores format_tools (used in step 2)
5. No behavior change yet — just wiring
```

## Commit Message
```
feat(icoder): add --no-format-tools CLI flag and plumbing (#763)

Thread format_tools bool from CLI parser through execute_icoder,
ICoderApp, and StreamEventRenderer constructor. No formatting
logic changes yet — just the wiring for the escape hatch.
```
