# Step 2: Shared executable finder utility

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 2 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Create a shared `find_executable()` utility in `src/mcp_coder/utils/executable_finder.py`. Then refactor `claude_executable_finder.py` to use it as the first-try step in its search. Follow TDD — write tests first, then implement.

## WHERE

### New files
- `src/mcp_coder/utils/executable_finder.py`
- `tests/utils/test_executable_finder.py`

### Modified files
- `src/mcp_coder/llm/providers/claude/claude_executable_finder.py`

## WHAT

### `src/mcp_coder/utils/executable_finder.py`
```python
def find_executable(name: str, *, install_hint: str) -> str:
    """Find executable by name via shutil.which().

    Args:
        name: Executable name (e.g. "copilot", "claude")
        install_hint: User-facing install instruction shown on failure

    Returns:
        Absolute path to the found executable.

    Raises:
        FileNotFoundError: If executable not found in PATH, with install_hint in message.
    """
```

### `src/mcp_coder/llm/providers/claude/claude_executable_finder.py`
In `_get_claude_search_paths()`, the existing `shutil.which()` call at the top is kept as-is (Claude has complex Windows `.exe` vs `.bat` logic that doesn't fit the generic utility). No change needed here — the shared utility is for simple PATH-only lookups like Copilot.

**Revised approach:** Leave `claude_executable_finder.py` unchanged. The shared utility exists for Copilot (and future providers that just need `shutil.which()`). Claude's finder already works and has provider-specific logic that shouldn't be abstracted.

## HOW

- `executable_finder.py` uses only `shutil.which` from stdlib — no project dependencies.
- Copilot's `copilot_cli.py` (Step 5) will call `find_executable("copilot", install_hint="...")`.

## ALGORITHM

```
1. Call shutil.which(name) (and shutil.which(name + ".exe") on Windows)
2. If found, return the path string
3. If not found, raise FileNotFoundError with install_hint in message
```

## DATA

- Input: `name: str`, `install_hint: str`
- Output: `str` (path to executable)
- Error: `FileNotFoundError` with descriptive message including `install_hint`

## Tests

### `tests/utils/test_executable_finder.py`

- `test_find_executable_found` — mock `shutil.which` returning a path, verify it's returned
- `test_find_executable_not_found` — mock `shutil.which` returning None, verify `FileNotFoundError` with install hint in message
- `test_find_executable_not_found_message_contains_name` — verify error mentions the executable name
- `test_find_executable_not_found_message_contains_hint` — verify error includes the install_hint
