# Step 5: /exit Alias for /quit

> **Reference:** See `pr_info/steps/summary.md` for full context.

## Goal

Register `/exit` as a second command that behaves identically to `/quit`.

## WHERE

- **Modify:** `src/mcp_coder/icoder/core/commands/quit.py`
- **Modify:** `tests/icoder/test_command_registry.py`

## WHAT

### `quit.py` — Register /exit alongside /quit

```python
def register_quit(registry: CommandRegistry) -> None:
    """Register the /quit and /exit commands."""

    @registry.register("/quit", "Exit iCoder")
    def handle_quit(args: list[str]) -> Response:  # noqa: ARG001
        return Response(quit=True)

    registry.register("/exit", "Exit iCoder")(handle_quit)
```

The `register()` decorator returns the original function, so we can call
`registry.register("/exit", ...)(handle_quit)` to register the same handler
under a second name.

### `test_command_registry.py` — Add /exit tests

New tests:

1. **`test_exit_command`**: `/exit` returns `quit=True`.
2. **`test_exit_in_help`**: `/exit` appears in `/help` output.
3. **Update `test_all_commands_registered`**: Expected set now includes `/exit`.

## HOW

- `registry.register(name, desc)` returns a decorator (callable).
- Calling that decorator with `handle_quit` registers it and returns `handle_quit`.
- No stacking decorators on the definition — explicit second call after.

## ALGORITHM

No algorithm — one extra registration call.

## DATA

No new types. Same `Response(quit=True)` return value.

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for full context.

Implement step 5: Register /exit as an alias for /quit in quit.py. Write tests first
in test_command_registry.py (test_exit_command, test_exit_in_help, update
test_all_commands_registered), then implement. Run all three MCP code quality checks
after changes. Commit message: "icoder: add /exit alias for /quit"
```
