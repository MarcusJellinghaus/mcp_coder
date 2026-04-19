# Step 1: SUPPORTED_PROVIDERS constant + update all consumers

**Reference:** See `pr_info/steps/summary.md` for full context (Issue #847).

## LLM Prompt

> Implement Step 1 of the Copilot CLI provider (issue #847). See `pr_info/steps/summary.md` for full context.
>
> Add a `SUPPORTED_PROVIDERS` frozenset to `src/mcp_coder/llm/types.py` and replace all hardcoded `["claude", "langchain"]` references across the codebase. Add `"copilot"` as the third provider. Update tests to cover the new provider value. Follow TDD — write/update tests first, then implement.

## WHERE

### Modified files
- `src/mcp_coder/llm/types.py`
- `src/mcp_coder/llm/session/resolver.py`
- `src/mcp_coder/cli/parsers.py`
- `src/mcp_coder/cli/utils.py`
- `tests/llm/test_types.py`
- `tests/llm/session/test_resolver.py`
- `tests/cli/test_parsers.py`
- `tests/cli/test_utils.py`
- `pyproject.toml` (add `copilot_cli_integration` marker)

## WHAT

### `src/mcp_coder/llm/types.py`
```python
SUPPORTED_PROVIDERS: frozenset[str] = frozenset({"claude", "langchain", "copilot"})
```
Add to `__all__`.

### `src/mcp_coder/llm/session/resolver.py`
```python
from ..types import SUPPORTED_PROVIDERS

def parse_llm_method(llm_method: str) -> str:
    if llm_method in SUPPORTED_PROVIDERS:
        return llm_method
    raise ValueError(
        f"Unsupported llm_method: {llm_method}. "
        f"Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
    )
```

### `src/mcp_coder/cli/parsers.py`
Replace all 8 occurrences of `choices=["claude", "langchain"]` with `choices=sorted(SUPPORTED_PROVIDERS)`. Import from `..llm.types`.

**Note:** This changes `--help` output for all 8 subcommands to show `[claude, copilot, langchain]`. Verify no snapshot/golden-file tests capture CLI help text.

### `src/mcp_coder/cli/utils.py`
Remove `_VALID_PROVIDERS = {"claude", "langchain"}`. Import and use `SUPPORTED_PROVIDERS` from `..llm.types`.

### `pyproject.toml`
Add marker:
```
"copilot_cli_integration: tests that use real Copilot CLI executable (slow)",
```

## HOW

- `parsers.py`: Add `from ..llm.types import SUPPORTED_PROVIDERS` at top (after `__future__` import).
- `utils.py`: Replace `from ..llm.session import parse_llm_method` is already there. Add `from ..llm.types import SUPPORTED_PROVIDERS`.
- `resolver.py`: Import from `..types` (relative within `llm` package).

## ALGORITHM

```
1. Define SUPPORTED_PROVIDERS = frozenset({"claude", "langchain", "copilot"})
2. In parse_llm_method: check membership, return or raise ValueError
3. In parsers.py: replace choices=["claude", "langchain"] → choices=sorted(SUPPORTED_PROVIDERS)
4. In utils.py: replace _VALID_PROVIDERS with SUPPORTED_PROVIDERS
5. Update all tests to verify "copilot" is accepted and unknown providers are rejected
```

## DATA

- `SUPPORTED_PROVIDERS`: `frozenset[str]` — `{"claude", "langchain", "copilot"}`
- `parse_llm_method("copilot")` → `"copilot"`
- `parse_llm_method("invalid")` → `ValueError`

## Tests

### `tests/llm/test_types.py`
- Test `SUPPORTED_PROVIDERS` contains exactly `{"claude", "langchain", "copilot"}`
- Test it's a frozenset (immutable)

### `tests/llm/session/test_resolver.py`
- Add `test_parse_copilot` — `parse_llm_method("copilot")` returns `"copilot"`
- Existing invalid-method tests remain (verify error message now mentions "copilot")

### `tests/cli/test_parsers.py`
- Add test that `--llm-method copilot` is accepted by the prompt parser
- Add test that `--llm-method invalid` is rejected

### `tests/cli/test_utils.py`
- Add test that `resolve_llm_method("copilot")` returns `("copilot", "cli argument")`
- Add test that `resolve_llm_method("invalid")` raises ValueError mentioning all three providers

### `tests/llm/test_interface.py`
- Update `test_prompt_llm_unsupported_provider_gpt` — verify error message now lists all three providers
