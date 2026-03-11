# Step 1: Extract `_get_status_symbols()` and Add Verify Parser

> **Context:** Read `pr_info/steps/summary.md` first for the full picture.

## Goal

Two small infrastructure changes that later steps depend on:
1. Move `_get_status_symbols()` to `cli/utils.py` so the verify formatter can use it.
2. Move the verify subparser from inline in `main.py` to `parsers.py` and add `--check-models`.

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

### WHERE: `tests/cli/commands/test_verify_parser.py` (new)

```python
class TestVerifyParser:
    def test_verify_parser_exists(self) -> None:
        """verify subcommand is registered."""
        ...
    def test_check_models_flag_default_false(self) -> None:
        """--check-models defaults to False."""
        ...
    def test_check_models_flag_set(self) -> None:
        """--check-models sets attribute to True."""
        ...
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

### 2. `src/mcp_coder/cli/parsers.py`

**WHAT:** Add `add_verify_parser(subparsers) -> None`

```python
def add_verify_parser(subparsers: Any) -> None:
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify CLI installation, LLM provider, and MLflow configuration",
        formatter_class=WideHelpFormatter,
    )
    verify_parser.add_argument(
        "--check-models",
        action="store_true",
        help="List available models for the configured LangChain backend (requires network)",
    )
```

### 3. `src/mcp_coder/cli/main.py`

**WHAT:** Replace inline `subparsers.add_parser("verify", ...)` with `add_verify_parser(subparsers)` call.

**HOW:**
- Add `add_verify_parser` to the import from `.parsers`
- Remove the line: `subparsers.add_parser("verify", help="Verify Claude CLI installation and configuration")`
- Add: `add_verify_parser(subparsers)`

### 4. `src/mcp_coder/llm/providers/claude/claude_cli_verification.py`

**WHAT:** Remove `_get_status_symbols()` definition (it now lives in `cli/utils.py`).

> The function is still used in this file in Step 2 when we refactor it.
> For now, just remove the definition. Step 2 will refactor the callers.
> **Alternative:** If we want this step to be self-contained and passing,
> we can import from `cli/utils.py` in this step and leave the usage as-is.

**HOW:** Replace the local definition with:
```python
from ...cli.utils import _get_status_symbols
```

> **Note:** This creates a temporary import from CLI into domain layer.
> Step 2 removes all `_get_status_symbols` usage from this file entirely
> (the domain function will return dicts, not formatted strings).
> To avoid the temporary cross-layer import, an alternative is to defer
> the removal to Step 2 and keep the duplicate for one step.

**Decision:** Keep the local copy in Step 1, delete it in Step 2 when the
function stops being called from this file. This avoids a cross-layer import.

## Checklist

- [ ] `_get_status_symbols()` in `cli/utils.py` with tests
- [ ] `add_verify_parser()` in `parsers.py` with `--check-models` flag
- [ ] `main.py` uses `add_verify_parser()` instead of inline parser
- [ ] All existing tests still pass
