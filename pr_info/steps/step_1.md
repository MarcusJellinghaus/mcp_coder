# Step 1: Add `install_hint` to LangChain verification results

> **Context**: See `pr_info/steps/summary.md` for the full plan (Issue #553).

## LLM Prompt

```
Implement Step 1 of Issue #553 (see pr_info/steps/summary.md).

Add `install_hint` fields to LangChain verification result dicts when packages are missing (`ok=False`).

Follow TDD: write tests first in tests/llm/providers/langchain/test_langchain_verification.py,
then implement in src/mcp_coder/llm/providers/langchain/verification.py.

Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- **Test**: `tests/llm/providers/langchain/test_langchain_verification.py`
- **Impl**: `src/mcp_coder/llm/providers/langchain/verification.py`

## WHAT — Tests to Add

Add a new test class `TestInstallHints` with these tests:

```python
class TestInstallHints:
    def test_langchain_core_missing_has_install_hint(self) -> None:
        """When langchain-core is not installed, result includes install_hint."""

    def test_backend_package_missing_has_install_hint(self) -> None:
        """When backend package is missing, result includes install_hint with correct pip name."""

    def test_mcp_adapters_missing_has_install_hint(self) -> None:
        """When langchain-mcp-adapters is missing, result includes install_hint."""

    def test_langgraph_missing_has_install_hint(self) -> None:
        """When langgraph is missing, result includes install_hint."""

    def test_installed_packages_have_no_install_hint(self) -> None:
        """When packages are installed, no install_hint key is present."""
```

## WHAT — Implementation Changes

No new functions. Add `install_hint` key to existing result dicts.

### Functions modified (signatures unchanged):

- `verify_langchain()` — add `install_hint` to `langchain_core` and `backend_package` entries when `ok=False`
- `_check_mcp_adapter_packages()` — add `install_hint` to `mcp_adapters` and `langgraph` entries when `ok=False`

## HOW — Integration

Pure data addition — no new imports, no new dependencies.

## ALGORITHM

For each package check that produces `ok=False`:

```
if not pkg_installed:
    entry["install_hint"] = "pip install <pip-package-name>"
```

Package name mapping (Python import → pip name):
- `langchain_core` → `langchain-core`
- `langchain_openai` → `langchain-openai`
- `langchain_anthropic` → `langchain-anthropic`
- `langchain_google_genai` → `langchain-google-genai`
- `langchain_mcp_adapters` → `langchain-mcp-adapters`
- `langgraph` → `langgraph`

## DATA — Return Value Changes

Before:
```python
{"ok": False, "value": "not installed"}
```

After:
```python
{"ok": False, "value": "not installed", "install_hint": "pip install langchain-core"}
```

When `ok=True`, the `install_hint` key is **absent** (not `None`).
