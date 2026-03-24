# Step 3: Conditional Claude display, inline hints, and install summary

> **Context**: See `pr_info/steps/summary.md` for the full plan (Issue #553).

## LLM Prompt

```
Implement Step 3 of Issue #553 (see pr_info/steps/summary.md).

Modify the verify orchestrator to:
1. Show Claude section conditionally based on active provider
2. Render inline install hints in _format_section()
3. Print an install summary block at the end

Follow TDD: write tests first, then implement.
Tests go in tests/cli/commands/test_verify_format_section.py and
tests/cli/commands/test_verify_orchestration.py.
Implementation in src/mcp_coder/cli/commands/verify.py.

Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- **Tests**: `tests/cli/commands/test_verify_format_section.py`, `tests/cli/commands/test_verify_orchestration.py`
- **Impl**: `src/mcp_coder/cli/commands/verify.py`

## WHAT — Tests to Add

### In `test_verify_format_section.py` — add to existing `TestFormatSection`:

```python
def test_install_hint_rendered_inline(self) -> None:
    """When entry has install_hint and ok=False, hint appears indented below."""

def test_no_install_hint_when_ok(self) -> None:
    """When entry has ok=True, no install hint line appears even if hint key exists."""
```

### In `test_verify_orchestration.py` — add new class `TestConditionalClaudeDisplay`:

```python
class TestConditionalClaudeDisplay:
    def test_langchain_active_cli_found_shows_oneliner(self) -> None:
        """When langchain active and CLI binary exists, show brief one-liner."""

    def test_langchain_active_cli_not_found_skips_claude_section(self) -> None:
        """When langchain active and CLI not found, no BASIC VERIFICATION section."""

    def test_claude_active_shows_full_section(self) -> None:
        """When claude active, show full BASIC VERIFICATION section as before."""
```

### In `test_verify_orchestration.py` — add new class `TestInstallSummaryBlock`:

```python
class TestInstallSummaryBlock:
    def test_summary_block_shown_for_missing_packages(self) -> None:
        """When langchain packages missing, INSTALL INSTRUCTIONS block appears."""

    def test_no_summary_block_when_all_installed(self) -> None:
        """When all packages installed, no INSTALL INSTRUCTIONS block."""
```

## WHAT — Implementation Changes

### New function:

```python
def _collect_install_hints(result: dict[str, Any]) -> list[str]:
    """Collect install_hint values from a verification result dict."""
```

### Modified functions (signatures unchanged):

- `_format_section()` — after each `[NO]` line, check for `install_hint` and append indented `→` line
- `execute_verify()` — conditional Claude section + summary block rendering

## HOW — Integration

- Import `find_claude_executable` from `claude_executable_finder` (already in the provider package) for the quick binary check when langchain is active.
- No new external dependencies.

## ALGORITHM

### `_format_section` addition (~3 lines):

```
for each entry:
    format line as before
    if ok is False and "install_hint" in entry:
        append "                          → {hint}"
```

### `_collect_install_hints` (~5 lines):

```
hints = []
for key, entry in result.items():
    if isinstance(entry, dict) and not entry.get("ok") and "install_hint" in entry:
        hints.append(entry["install_hint"])
return hints
```

### Conditional Claude in `execute_verify` (~10 lines):

```
if active_provider == "claude":
    claude_result = verify_claude()
    print(_format_section("BASIC VERIFICATION", claude_result, symbols))
else:
    claude_path = find_claude_executable(return_none_if_not_found=True)
    if claude_path:
        print(f"\n  Claude CLI: available at {claude_path} (not active)")
    # else: skip entirely
    claude_result = {"overall_ok": True}  # neutral for exit code
```

### Summary block in `execute_verify` (~8 lines):

```
all_hints = []
if langchain_result:
    all_hints.extend(_collect_install_hints(langchain_result))
if active_provider == "claude":
    all_hints.extend(_collect_install_hints(claude_result))

if all_hints:
    pip_packages = " ".join(h.replace("pip install ", "") for h in all_hints if h.startswith("pip install"))
    print("\n=== INSTALL INSTRUCTIONS ===")
    print(f"  pip install {pip_packages}")
```

## DATA

### `_collect_install_hints` return:

```python
["pip install langchain-core", "pip install langgraph"]  # only missing ones
```

### Summary block output example:

```
=== INSTALL INSTRUCTIONS ===
  pip install langchain-core langgraph
```
