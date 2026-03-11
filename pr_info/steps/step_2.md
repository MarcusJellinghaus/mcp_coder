# Step 2: Refactor Claude CLI Verification to Return Dict

> **Context:** Read `pr_info/steps/summary.md` and Step 1 first.
> See `pr_info/steps/Decisions.md` — Decisions 1, 2, 7.

## Goal

Refactor `claude_cli_verification.py` so it returns a structured dict instead
of printing directly. The CLI layer (Step 5) will handle all formatting.

Also moves `_get_status_symbols()` to `cli/utils.py` (deferred from Step 1).

## Tests First

### WHERE: `tests/cli/test_utils_status_symbols.py` (new)

```python
class TestGetStatusSymbols:
    def test_returns_dict_with_required_keys(self) -> None:
        ...
    def test_windows_uses_ascii(self) -> None:
        ...
    def test_unix_uses_unicode(self) -> None:
        ...
```

### WHERE: `tests/llm/providers/claude/test_claude_cli_verification.py` (update existing or new)

```python
class TestVerifyClaude:
    @patch("mcp_coder.llm.providers.claude.claude_cli_verification._verify_claude_before_use")
    @patch("mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation")
    def test_returns_structured_dict(self, mock_basic, mock_advanced) -> None:
        mock_basic.return_value = {"found": True, "path": "/usr/bin/claude", "version": "2.1.40", "works": True, "error": None}
        mock_advanced.return_value = (True, "/usr/bin/claude", None)
        result = verify_claude()
        assert result["cli_found"]["ok"] is True
        assert result["cli_version"]["value"] == "2.1.40"
        assert result["api_integration"]["ok"] is True

    def test_cli_not_found(self, ...) -> None:
        ...  # found=False → cli_found.ok=False

    def test_api_integration_fails(self, ...) -> None:
        ...  # advanced returns (False, None, "error msg")

    def test_api_integration_exception(self, ...) -> None:
        ...  # advanced raises Exception
```

## Implementation

### 1. `src/mcp_coder/cli/utils.py`

**WHAT:** Add `_get_status_symbols() -> dict[str, str]`

**HOW:** Move the function body from `claude_cli_verification.py`. Add to `__all__`.

```python
def _get_status_symbols() -> dict[str, str]:
    if sys.platform.startswith("win"):
        return {"success": "[OK]", "failure": "[NO]", "warning": "[!!]"}
    else:
        return {"success": "✓", "failure": "✗", "warning": "⚠"}
```

**DATA:** Returns `{"success": str, "failure": str, "warning": str}`

### 2. `src/mcp_coder/llm/providers/claude/claude_cli_verification.py`

**WHAT:** Replace `verify_claude_cli_installation(args) -> int` with `verify_claude() -> dict`

This is a **clean break rename** (Decision 7) — no alias for the old name.

**SIGNATURE:**
```python
def verify_claude() -> dict[str, dict[str, Any]]:
```

**ALGORITHM:**
```
1. Call verify_claude_installation() → basic result dict
2. Build output dict from basic: cli_found, cli_path, cli_version, cli_works
3. Try _verify_claude_before_use() → (success, path, error)
4. Add api_integration entry to output dict
5. Add overall_ok = found AND works AND api_success
6. Return dict
```

**DATA — Return structure:**
```python
{
    "cli_found":        {"ok": bool, "value": "YES"/"NO"},
    "cli_path":         {"ok": True, "value": "/path/to/claude"},      # only if found
    "cli_version":      {"ok": True, "value": "2.1.40"},               # only if has version
    "cli_works":        {"ok": bool, "value": "YES"/"NO"},
    "api_integration":  {"ok": bool, "value": "OK"/"FAILED", "error": str|None},
    "overall_ok":       bool,
}
```

**HOW — Remove from this file:**
- Delete `_get_status_symbols()` definition (moved to `cli/utils.py` above)
- Delete all `print()` calls
- Delete the `argparse.Namespace` parameter (no longer needed)
- Remove `import argparse` and `import sys` (no longer needed)

### 3. `src/mcp_coder/cli/commands/verify.py` (temporary shim)

Keep `execute_verify(args)` working by adapting it to the new return type.
This will be fully rewritten in Step 5, but we need tests to pass here.

```python
def execute_verify(args: argparse.Namespace) -> int:
    from ...llm.providers.claude.claude_cli_verification import verify_claude
    from ..utils import _get_status_symbols
    result = verify_claude()
    # Minimal output until Step 5 rewrites this
    symbols = _get_status_symbols()
    print("=== BASIC VERIFICATION ===")
    for key, entry in result.items():
        if key == "overall_ok":
            continue
        if isinstance(entry, dict):
            status = symbols["success"] if entry.get("ok") else symbols["failure"]
            print(f"{key}: {status} {entry.get('value', '')}")
    return 0 if result.get("overall_ok") else 1
```

### 4. Update all test references

**Clean break (Decision 7):** Update all existing test files that reference
`verify_claude_cli_installation` to use `verify_claude` instead. This includes:
- `tests/cli/commands/test_verify.py`
- `tests/cli/commands/test_verify_command.py`
- Any other files that import or mock the old function name

## Checklist

- [ ] `_get_status_symbols()` moved to `cli/utils.py` with tests
- [ ] `verify_claude()` returns structured dict (no print calls)
- [ ] Old `_get_status_symbols()` deleted from `claude_cli_verification.py`
- [ ] Old `verify_claude_cli_installation` name removed — all references updated
- [ ] `execute_verify()` shim keeps CLI working
- [ ] New unit tests for dict return values
- [ ] Existing verify tests updated and passing
