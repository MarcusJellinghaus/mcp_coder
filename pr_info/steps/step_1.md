# Step 1: Add Verify Parser to `parsers.py`

> **Context:** Read `pr_info/steps/summary.md` first for the full picture.
> See `pr_info/steps/Decisions.md` — Decision 1: `_get_status_symbols()` move deferred to Step 2.

## Goal

One infrastructure change that later steps depend on:
Move the verify subparser from inline in `main.py` to `parsers.py` and add `--check-models`.

## Tests First

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

### 1. `src/mcp_coder/cli/parsers.py`

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

### 2. `src/mcp_coder/cli/main.py`

**WHAT:** Replace inline `subparsers.add_parser("verify", ...)` with `add_verify_parser(subparsers)` call.

**HOW:**
- Add `add_verify_parser` to the import from `.parsers`
- Remove the line: `subparsers.add_parser("verify", help="Verify Claude CLI installation and configuration")`
- Add: `add_verify_parser(subparsers)`

## Checklist

- [ ] `add_verify_parser()` in `parsers.py` with `--check-models` flag
- [ ] `main.py` uses `add_verify_parser()` instead of inline parser
- [ ] All existing tests still pass
