# Step 1: Add `filter_by_input()` to `CommandRegistry`

> **Context:** See `pr_info/steps/summary.md` for full issue context and architecture.

## Goal

Add a pure method to `CommandRegistry` that returns matching commands for autocomplete. TDD: write tests first, then implement.

## WHERE

| Action | File |
|--------|------|
| Modify | `tests/icoder/test_command_registry.py` |
| Modify | `src/mcp_coder/icoder/core/command_registry.py` |

## WHAT

```python
# In CommandRegistry class
def filter_by_input(self, input_text: str) -> list[Command]:
    """Return commands matching input_text for autocomplete."""
```

## HOW

- Method lives on the existing `CommandRegistry` class
- No new imports, no Textual dependency
- Uses `self._commands` dict that already exists

## ALGORITHM

```python
def filter_by_input(self, input_text: str) -> list[Command]:
    if not input_text.startswith("/"):
        return []
    prefix = input_text.split()[0].lower()  # safe: startswith("/") implies non-empty
    return sorted(
        [c for c in self._commands.values() if c.name.lower().startswith(prefix)],
        key=lambda c: c.name,
    )
```

## DATA

- **Input:** `input_text: str` — raw text from the input area
- **Output:** `list[Command]` — matching commands, sorted by name for stable ordering
- Empty list if input doesn't start with `/`

## Tests (write first)

Add to `tests/icoder/test_command_registry.py`:

```python
def test_filter_by_input_slash_returns_all() -> None:
    """filter_by_input('/') returns all registered commands."""
    registry = create_default_registry()
    result = registry.filter_by_input("/")
    names = {c.name for c in result}
    assert names == {"/help", "/clear", "/quit"}

def test_filter_by_input_prefix_match() -> None:
    """filter_by_input('/he') returns [/help]."""
    registry = create_default_registry()
    result = registry.filter_by_input("/he")
    assert len(result) == 1
    assert result[0].name == "/help"

def test_filter_by_input_case_insensitive() -> None:
    """filter_by_input('/HE') returns [/help] (case-insensitive)."""
    registry = create_default_registry()
    result = registry.filter_by_input("/HE")
    assert len(result) == 1
    assert result[0].name == "/help"

def test_filter_by_input_no_match() -> None:
    """filter_by_input('/xyz') returns []."""
    registry = create_default_registry()
    assert registry.filter_by_input("/xyz") == []

def test_filter_by_input_empty_string() -> None:
    """filter_by_input('') returns [] (not a command prefix)."""
    registry = create_default_registry()
    assert registry.filter_by_input("") == []

def test_filter_by_input_no_slash() -> None:
    """filter_by_input('hello') returns [] (doesn't start with '/')."""
    registry = create_default_registry()
    assert registry.filter_by_input("hello") == []

def test_filter_by_input_sorted() -> None:
    """filter_by_input results are sorted by command name."""
    registry = create_default_registry()
    result = registry.filter_by_input("/")
    names = [c.name for c in result]
    assert names == sorted(names)
```

## Commit

`feat(icoder): add filter_by_input to CommandRegistry`

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement Step 1.

1. Add the test functions listed in step_1.md to tests/icoder/test_command_registry.py
2. Run tests — they should FAIL (method doesn't exist yet)
3. Add filter_by_input() to CommandRegistry in src/mcp_coder/icoder/core/command_registry.py
4. Run all three quality checks (pylint, pytest, mypy) — all must pass
5. Commit: "feat(icoder): add filter_by_input to CommandRegistry"
```
