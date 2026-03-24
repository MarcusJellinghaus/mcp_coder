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
```

```python
class TestCollectInstallHints:
    def test_collects_hints_from_failed_entries(self) -> None:
        """Collects install_hint values from entries with ok=False."""

    def test_skips_entries_without_hint(self) -> None:
        """Entries with ok=False but no install_hint key are skipped."""

    def test_skips_ok_entries(self) -> None:
        """Entries with ok=True are skipped even if install_hint is present."""

    def test_skips_non_dict_entries(self) -> None:
        """Non-dict entries (like overall_ok bool) are skipped."""
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

### Existing Tests to Update

These tests currently mock `verify_claude()` when langchain is active. After this step, `verify_claude()` is no longer called when `active_provider == "langchain"` — the quick binary check replaces it. Each test needs its mock setup adjusted:

- `test_all_sections_printed` — currently expects "BASIC VERIFICATION" in output when langchain is active. Update to expect the one-liner or no Claude section instead.
- `test_claude_informational_when_langchain_active` — currently patches `verify_claude`. Update to patch `find_claude_executable` instead, and assert the one-liner output.
- `test_exit_1_when_active_provider_fails` — the `verify_claude` mock becomes unused when langchain is active. Verify the test still makes sense or split into provider-specific exit code tests.

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

- Import: `from mcp_coder.llm.providers.claude.claude_executable_finder import find_claude_executable` (use relative import `from ...llm.providers.claude.claude_executable_finder import find_claude_executable` to match file conventions).
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

**Note**: The `pip install` summary block only collects hints starting with `"pip install"`. The Claude docs URL hint (from Step 2) is naturally excluded. When `active_provider == "langchain"`, Claude hints are not collected at all (consistent with issue requirement: "Only show install hints for the active provider's missing dependencies").

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
