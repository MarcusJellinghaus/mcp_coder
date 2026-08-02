# Step 4 — Blocked-skill handling: refuse to run + mark in autocomplete

**Read `pr_info/steps/summary.md` first.** A skill whose declaration is broken (D7: fatal `errors`;
`base:none` with nothing surviving; bare `use:`) must **refuse to run** with its reason rather than
burn an LLM turn on a confused answer — while staying **registered and visible** (this is *not*
`load_skills`'s warn-and-skip ladder). Blocked-ness is already computed once as
`SkillFrame.blocked_reason` (Step 2); this step surfaces it on `Command.disabled_reason` (the generic
type the autocomplete already renders) and refuses at the single `handle_input` dispatch hop (design
§3 / #1040 boundary).

## WHERE (all modified)
- `src/mcp_coder/icoder/core/types.py` — `Command.disabled_reason: str | None = None`
- `src/mcp_coder/icoder/core/command_registry.py` — add `get(name) -> Command | None`
- `src/mcp_coder/icoder/skills.py` — `register_skill_commands(..., disabled_reasons=...)`
- `src/mcp_coder/icoder/core/app_core.py` — refuse blocked commands in `handle_input`
- `src/mcp_coder/cli/commands/icoder.py` — pass `disabled_reasons` from the frame map
- `src/mcp_coder/icoder/ui/widgets/command_autocomplete.py` — mark disabled rows
- Tests: `tests/icoder/test_types.py`, `test_command_registry.py`, `test_skills.py`,
  `test_app_core.py`, `test_command_autocomplete.py`, `test_cli_icoder.py`

## WHAT (signatures)
```python
# core/types.py
class Command: name: str; description: str; handler: ...; show_in_help: bool = True
               disabled_reason: str | None = None      # non-None → command exists but refuses to run

# command_registry.py
def get(self, name: str) -> Command | None: ...

# skills.py
def register_skill_commands(
    registry: CommandRegistry, skills: list[ClaudeSkill], provider: str,
    disabled_reasons: Mapping[str, str | None] | None = None,
) -> list[ICoderSkillCommand]: ...
```

## HOW
- **`skills.py`:** when building each `Command`, set `disabled_reason=(disabled_reasons or {}).get(skill.name)`.
  Signature-compatible: existing callers that omit the arg get `None` (claude branch unaffected).
- **`cli/commands/icoder.py`:** langchain branch passes
  `disabled_reasons={n: f.blocked_reason for n, f in frame_map.items()}` into `register_skill_commands`.
  (The map already exists from Step 3.)
- **`app_core.py` `handle_input`:** *before* dispatch, if the leading token names a registered command
  whose `disabled_reason` is set, emit `output_emitted` and return `Response((OutputText(reason),))` —
  **no dispatch, no `SendToLLM`**. Keep the existing `command_matched` / dispatch path otherwise. This
  reuses the same hop that already rewrites `SendToLLM`.
- **`command_autocomplete.py`:** in `update_matches`, render a disabled command as
  `Option(f"{cmd.name} - {cmd.description}  (disabled: {cmd.disabled_reason})", id=cmd.name, disabled=True)`
  so it shows but cannot be selected (`select_highlighted` already returns `None` for disabled options).

## ALGORITHM (`handle_input`, new guard near the top of the command path)
```
text = text.strip()
if not text: return Response()
self._event_log.emit("input_received", text=text)
lead = text.split()[0].lower()
cmd = self._registry.get(lead)
if cmd is not None and cmd.disabled_reason:
    self._event_log.emit("output_emitted", text=cmd.disabled_reason)
    return Response((OutputText(cmd.disabled_reason),))
# ... existing dispatch as before ...
```

## DATA
- `Command.disabled_reason` is the **single** blocked signal, read by both the autocomplete and the
  refusal. `SkillFrame` remains unchanged from Step 2 (its `blocked_reason` feeds this field at startup).
- A blocked command dispatches **no** `SendToLLM`; the UI never enters "Querying LLM…".

## TESTS (write first)
- `test_types.py`: `Command.disabled_reason` defaults `None`.
- `test_command_registry.py`: `get("/x")` returns the command or `None`.
- `test_skills.py`: `register_skill_commands(..., disabled_reasons={"foo":"broken"})` yields a `Command`
  with `disabled_reason == "broken"`; the command is still registered/visible.
- `test_app_core.py`: invoking a blocked command returns a single `OutputText(reason)` and **no**
  `SendToLLM`; a non-blocked command is unaffected; an `output_emitted` event is logged.
- `test_command_autocomplete.py`: a disabled command appears as a disabled option and
  `select_highlighted()` on it returns `None`.
- `test_cli_icoder.py`: under langchain, a skill with a malformed `tools:` block ends up with a
  non-`None` `disabled_reason` on its registered command.

## LLM PROMPT
> Implement Step 4 of `pr_info/steps/summary.md` (see `pr_info/steps/step_4.md`). Using TDD, write the
> listed tests first, then: add `Command.disabled_reason`; add `CommandRegistry.get`; give
> `register_skill_commands` an optional `disabled_reasons` mapping and set `disabled_reason` at Command
> creation; in `cli/commands/icoder.py` pass `{name: SkillFrame.blocked_reason}` from the frame map;
> add the pre-dispatch refusal guard to `AppCore.handle_input` (return `OutputText(reason)`, dispatch
> nothing); and mark disabled commands in `command_autocomplete.update_matches`. Run pylint,
> mypy(strict), pytest (`-n auto` unit-only exclusions) and `lint-imports` until green. One commit.
