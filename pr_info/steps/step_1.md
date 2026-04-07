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

```
def filter_by_input(self, input_text: str) -> list[Command]:
    if not input_text.startswith("/"):
        return []
    prefix = input_text.split()[0].lower()  # first word, lowered
    return [cmd for cmd in self._commands.values()
            if cmd.name.lower().startswith(prefix)]
```

Note: use `input_text.split()[0]` to handle cases like `/he ` (with trailing space) — only match on the first word. But actually, for autocomplete the user types `/he` and hasn't submitted yet, so the full `input_text` might be just `/he`. We should match the prefix of the first word: extract everything from `/` up to the first space (or end of string), lowercase it, and prefix-match against command names.

Refined:
```
prefix = input_text.split()[0].lower() if input_text.strip() else ""
if not prefix.startswith("/"):
    return []
return sorted matching commands by name
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
    assert names == {"/help", "/clear", "/quit", "/exit"}

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
