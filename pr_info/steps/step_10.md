# Step 10 — `/display` command + `--tool-display` CLI flag + `RebuildOutput` action + `/help` text

## Goal

User-facing entry points for the new feature:
- New slash command `/display oneline|compressed` — hard reset (set default + wipe overrides).
- New CLI flag `--tool-display=oneline|compressed` (default `compressed`) — sets initial value.
- New `RebuildOutput` action — dispatched by `/display` to trigger `output.rebuild()`.
- `/help` text updated to mention `F2`.

## WHERE

- `src/mcp_coder/icoder/core/types.py` — add `RebuildOutput` to the `Action` union
- `src/mcp_coder/icoder/core/app_core.py` — add `tool_display` field + `set_tool_display()` method
- `src/mcp_coder/icoder/core/commands/display.py` — new file: `/display` registration
- `src/mcp_coder/icoder/core/commands/__init__.py` — export `register_display`
- `src/mcp_coder/icoder/core/command_registry.py` — wire `register_display(registry, app_core)` into the default registry
- `src/mcp_coder/icoder/core/commands/help.py` — append the F2 hint line
- `src/mcp_coder/icoder/ui/app.py` — dispatch `RebuildOutput` → `output.set_tool_display_default(...)` (which both updates default and triggers rebuild)
- `src/mcp_coder/cli/parsers.py` — `--tool-display` option in `add_icoder_parser`
- `src/mcp_coder/cli/commands/icoder.py` — thread arg to `AppCore(...)` constructor
- `docs/icoder/icoder.md` — add tier section + `/display` row + F2 to shortcuts
- `tests/icoder/test_display_command.py` — new file
- `tests/icoder/test_app_core.py` — add `tool_display` field tests
- `tests/icoder/test_cli_icoder_parser.py` — add `--tool-display` arg test
- `tests/icoder/test_help_command.py` (or similar existing) — assert F2 line present

## WHAT

```python
# core/types.py
@dataclass(frozen=True)
class RebuildOutput: pass

Action = Quit | ClearOutput | OpenPicker | ResetSession | SendToLLM | OutputText | RebuildOutput

# core/app_core.py
class AppCore:
    def __init__(self, ..., tool_display: Literal["oneline","compressed"] = "compressed") -> None:
        ...
        self._tool_display = tool_display

    @property
    def tool_display(self) -> str: return self._tool_display

    def set_tool_display(self, value: Literal["oneline","compressed"]) -> None:
        self._tool_display = value
        self._event_log.emit("display_mode_changed", to=value)

# core/commands/display.py
def register_display(registry: CommandRegistry, app_core: AppCore) -> None:
    @registry.register("/display", "Set default tool display tier (oneline|compressed)")
    def handle_display(args: list[str]) -> Response:
        if not args or args[0] not in ("oneline", "compressed"):
            return Response(actions=(OutputText(text="Usage: /display oneline|compressed"),))
        previous = app_core.tool_display
        app_core.set_tool_display(args[0])
        # Event already emitted by AppCore; RebuildOutput triggers OutputLog reset.
        return Response(actions=(RebuildOutput(),))
```

## HOW

- App dispatch (in `on_input_area_input_submitted`) adds:
  ```python
  case RebuildOutput():
      output.set_tool_display_default(self._core.tool_display)
  ```
  `set_tool_display_default` (from step 6) already wipes overrides + triggers rebuild.
- CLI plumbing (mirror `--initial-color`):
  - `parsers.py`: `icoder_parser.add_argument("--tool-display", choices=["oneline","compressed"], default="compressed", help="Default tier for tool display blocks")`.
  - `cli/commands/icoder.py`: read `args.tool_display`, pass as `tool_display=args.tool_display` to `AppCore(...)`.
  - `ICoderApp.on_mount` (or wherever `OutputLog` is initialized): after compose, call `output.set_tool_display_default(self._core.tool_display)` so the initial value matches the CLI flag.
- `/help` text: in `register_help` (`core/commands/help.py`), append a line `"  F2          - Open detail view for the most recent content"` to the keyboard-shortcuts section.

## ALGORITHM

`/display` is a simple validate-and-set:

```
args = handler args
if not args or args[0] not in {oneline, compressed}:
    return Response(actions=(OutputText(text="Usage: /display oneline|compressed"),))
app_core.set_tool_display(args[0])
return Response(actions=(RebuildOutput(),))
```

## DATA

- `AppCore.tool_display: str` (always "oneline" or "compressed").
- Event emitted: `display_mode_changed` with `to=value`.

## TDD

`tests/icoder/test_display_command.py` (new):

1. `test_display_oneline_returns_rebuild_action`
2. `test_display_compressed_returns_rebuild_action`
3. `test_display_no_args_returns_usage_message` — `Response(actions=(OutputText(text="Usage: ..."),))`
4. `test_display_invalid_arg_returns_usage_message`
5. `test_display_updates_app_core_tool_display`
6. `test_display_emits_display_mode_changed_event`

`tests/icoder/test_app_core.py` additions:

7. `test_app_core_default_tool_display_is_compressed`
8. `test_app_core_set_tool_display_changes_value`
9. `test_app_core_init_with_tool_display_oneline_sets_field`

`tests/icoder/test_cli_icoder_parser.py` additions:

10. `test_tool_display_arg_default_compressed`
11. `test_tool_display_arg_accepts_oneline`
12. `test_tool_display_arg_rejects_unknown_value`

`tests/icoder/test_app_pilot.py` additions:

13. `test_display_oneline_rebuilds_all_tool_units_as_oneline` — emit some tool units (compressed), submit `/display oneline`, all rendered_lines for those units are oneline.
14. `test_display_compressed_wipes_per_unit_overrides` — toggle a tool to oneline manually; submit `/display compressed`; that tool is back to compressed in rendered_lines.

`tests/icoder/test_help_command.py`:

15. `test_help_mentions_f2`

Update `docs/icoder/icoder.md`:
- New section `### Tool Display Tiers` describing the three tiers and the toggle behavior.
- Add `/display` row to the Slash Commands table.
- Add `F2` row to the Input Behaviour table.

Then implement.

## Code quality gates

Pylint, pytest, mypy — all green.

Add snapshot tests in `tests/icoder/test_snapshots.py`:

- `test_snapshot_default_tier` (compressed)
- `test_snapshot_after_display_oneline`
- `test_snapshot_modal_over_tool`

Re-baseline once authored.

## LLM Prompt

> Implement **Step 10** from `pr_info/steps/step_10.md` (`/display` + `--tool-display` + `RebuildOutput`).
>
> Read `pr_info/steps/summary.md` first for context.
>
> Constraints:
> - Add `RebuildOutput` to the `Action` union (the one action deferred from step 1).
> - `/display` validates args (`oneline` / `compressed` only); usage message on bad input.
> - `AppCore.tool_display` defaults to `"compressed"`. Setter emits `display_mode_changed` event.
> - CLI flag `--tool-display` mirrors `--initial-color`'s plumbing.
> - On mount, `OutputLog.set_tool_display_default(self._core.tool_display)` so the initial state matches the CLI flag.
> - `/help` text gets an F2 line.
> - Docs: `docs/icoder/icoder.md` gets a tier section + `/display` row + F2 row.
> - TDD: 15 test cases first, then implement.
> - Add 3 snapshot tests (default, after `/display oneline`, modal-over-tool); re-baseline as needed.
>
> All three quality gates green after the change. This is the final step — the feature is complete.
