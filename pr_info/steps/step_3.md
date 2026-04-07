# Step 3: Pure `core/autocomplete_state.py` Module

> **Context:** See `pr_info/steps/summary.md` for full context. See `Decisions.md` D1 for the state-representation choice.

## Goal

Create a pure (no Textual) module that defines the autocomplete state and a function to compute the next state from raw input. This is the "state machine" referenced in the issue, expressed as a frozen dataclass + pure function (Decision D1).

The InputArea (Step 4) calls `compute_next_state()` on every text change and diffs the previous vs new state to drive the dropdown and emit events. Because this module is pure, it is unit-testable without a Textual pilot.

## WHERE

| Action | File |
|--------|------|
| Create | `src/mcp_coder/icoder/core/autocomplete_state.py` |
| Create | `tests/icoder/test_autocomplete_state.py` |

## WHAT

```python
from dataclasses import dataclass

from mcp_coder.icoder.core.command_registry import CommandRegistry
from mcp_coder.icoder.core.types import Command


@dataclass(frozen=True)
class AutocompleteState:
    """Snapshot of autocomplete state for a given input text."""

    visible: bool
    matches: tuple[Command, ...]
    highlighted_index: int  # 0 when matches non-empty, -1 when empty


def compute_next_state(
    input_text: str,
    registry: CommandRegistry,
) -> AutocompleteState:
    """Compute the autocomplete state for the given input text.

    Pure function — no I/O, no Textual dependency.
    """
```

## ALGORITHM

```python
def compute_next_state(input_text, registry):
    if not input_text.startswith("/"):
        return AutocompleteState(visible=False, matches=(), highlighted_index=-1)
    matches = tuple(registry.filter_by_input(input_text))
    return AutocompleteState(
        visible=True,
        matches=matches,
        highlighted_index=0 if matches else -1,
    )
```

## DATA

- **Input:** `input_text: str`, `registry: CommandRegistry`.
- **Output:** `AutocompleteState` (frozen dataclass).
- Invariant: `visible == input_text.startswith("/")`.
- Invariant: `highlighted_index == 0` iff `matches` is non-empty, else `-1`.
- The dropdown is **visible even when matches is empty** (for the `/xyz` "no matching commands" case).

## Tests (write first)

`tests/icoder/test_autocomplete_state.py` — pure unit tests, no Textual:

```python
def test_hidden_when_text_does_not_start_with_slash() -> None:
    """Empty string and non-slash text → visible=False, no matches."""

def test_visible_with_all_commands_when_text_is_slash() -> None:
    """'/' → visible=True, matches contains all 3 commands, highlighted_index=0."""

def test_visible_with_filtered_matches_on_he_prefix() -> None:
    """'/he' → visible=True, matches=(/help,), highlighted_index=0."""

def test_visible_with_empty_matches_on_unknown_prefix() -> None:
    """'/xyz' → visible=True, matches=(), highlighted_index=-1."""

def test_highlighted_index_zero_when_matches_present() -> None:
    """Any state with non-empty matches has highlighted_index == 0."""

def test_highlighted_index_minus_one_when_no_matches() -> None:
    """Any state with empty matches has highlighted_index == -1."""

def test_state_is_frozen_and_replaced_not_mutated() -> None:
    """AutocompleteState is frozen — replacement is via new instance, not mutation."""
```

Use `create_default_registry()` to build the registry fixture.

## Caller usage (preview, implemented in Step 4)

```python
prev = self._ac_state
new = compute_next_state(text, registry)
self._ac_state = new
# Diff prev vs new to emit autocomplete_shown / hidden / filtered events.
```

## Commit

`feat(icoder): add autocomplete state module`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/Decisions.md (D1) for context, then implement Step 3.

1. Create tests/icoder/test_autocomplete_state.py with the 7 tests above (TDD).
2. Create src/mcp_coder/icoder/core/autocomplete_state.py with AutocompleteState frozen dataclass and compute_next_state() pure function.
3. Run all five quality checks — all must pass.
4. Commit: "feat(icoder): add autocomplete state module"
```
