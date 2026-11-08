# Summary — Make the LangChain model layer self-contained (#1396)

Step 1 of MarcusJellinghaus/agent-workbench#12. agent-workbench copies mcp_coder's
LangChain **model layer** unchanged and replaces only one product-texts module.
Files stay where they are; no behaviour change; `mcp-coder verify` output stays
byte-identical.

## Model layer (all in `src/mcp_coder/llm/providers/langchain/`)

`anthropic_backend`, `gemini_backend`, `ollama_backend`, `openai_backend`,
`_models`, `_setup`, `_http`, `_exceptions`, `_errors_404`, `_usage`,
`_preflight`, `_config_diagnostics`, `_messages`, **new** `_provider_checks`,
**new** `_product`.

Outside it (glue / MCP): `__init__`, `agent`, `_mcp_tools`, `mcp_manager`,
`approval_bridge`, `permission_bridge`, `verification`, **new** `_config_source`.

Allowed mcp_coder imports from the model layer: `mcp_coder.llm.types`,
`mcp_coder.utils.config_hints`, `mcp_coder.utils.log_utils`.

## Architectural / design changes

| Change | Before | After |
|---|---|---|
| Config loading | `_setup._load_langchain_config` reads `utils.user_config` | Moves to new `_config_source.py` (outside model layer). `__init__` re-exports it, `verification` imports it as a module-level name. `_create_chat_model(config, ...)` already receives config as an argument. |
| Session id | `_setup._resolve_session_id` uses session storage | Moves into `__init__` (already imports session storage). |
| `resolve_target` | lazy `from . import _create_chat_model` (package `__init__`) | lazy `from ._setup import _create_chat_model` (cycle disable kept). |
| Provider checks | all inside `verification.verify_langchain` | New `_provider_checks.check_provider(config, check_models=False) -> dict` produces every row except the MCP rows, plus its own `overall_ok`. Moved helpers live **only** there (no re-exports). |
| `verify_langchain` | builds everything | load config → `check_provider` → `_check_mcp_adapter_packages` → re-insert MCP rows before the first probe row (or before `overall_ok`) → combine `overall_ok`. Signature unchanged. |
| Product texts | literals spread over 7 modules | New `_product.py` with four constants: `INSTALL_HINT`, `OLLAMA_INSTALL_HINT`, `CONFIG_SECTION`, `PRODUCT_NAME` (today's exact values). |
| Boundary | none | Two import-linter contracts: an allowlist (wildcards + `ignore_imports` for the three allowed modules) and an ancestor contract with `as_packages = False`. |

KISS choices:
- Contracts are written once, after all code moves (step 7), so no contract is edited three times.
- MCP rows are re-inserted by one small loop over `_PROBE_KEYS`; `check_provider` has no hook parameter.
- `_product.py` holds plain literals, none derived from another.
- No value-pinning test for `_product.py`: existing exact-text tests already pin every rendered string.

## Steps

1. Key-order test for `verify_langchain` (before any change).
2. Move `_load_langchain_config` to `_config_source.py`.
3. Move `_resolve_session_id` into `__init__`.
4. `resolve_target` imports `_create_chat_model` from `._setup`.
5. Split `verification.py` → `_provider_checks.py`.
6. Product texts → `_product.py`.
7. Import-linter contracts + `import-linter>=2.15`.
8. Architecture documentation.

## Files

**Created**
- `src/mcp_coder/llm/providers/langchain/_config_source.py`
- `src/mcp_coder/llm/providers/langchain/_provider_checks.py`
- `src/mcp_coder/llm/providers/langchain/_product.py`
- `tests/llm/providers/langchain/test_langchain_verify_row_order.py`
- `tests/llm/providers/langchain/test_langchain_provider_checks.py`
- `tests/llm/providers/langchain/test_langchain_verification_mcp_split.py`
- `tests/llm/providers/langchain/test_langchain_config_source.py`

**Modified (production)**
- `src/mcp_coder/llm/providers/langchain/__init__.py`
- `src/mcp_coder/llm/providers/langchain/_setup.py`
- `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py`
- `src/mcp_coder/llm/providers/langchain/verification.py`
- `src/mcp_coder/llm/providers/langchain/{anthropic,gemini,ollama,openai}_backend.py`
- `src/mcp_coder/llm/providers/langchain/_models.py`
- `src/mcp_coder/llm/providers/langchain/_preflight.py`
- `src/mcp_coder/llm/providers/langchain/_errors_404.py`
- `src/mcp_coder/cli/commands/verify_sections.py`
- `.importlinter`
- `pyproject.toml`
- `docs/architecture/architecture.md`

**Modified (tests, patch targets / imports only)**
- `tests/llm/providers/langchain/conftest.py`
- `tests/llm/providers/langchain/test_langchain_provider.py`
- `tests/llm/providers/langchain/test_langchain_resolve_target.py`
- `tests/llm/providers/langchain/test_langchain_base_url_shape.py`
- `tests/llm/providers/langchain/test_langchain_verification.py`
- `tests/llm/providers/langchain/test_langchain_verification_ollama.py`
- `tests/llm/providers/langchain/test_langchain_effective_config.py`
- `tests/llm/providers/langchain/test_langchain_contract_rows.py`
- `tests/llm/providers/langchain/test_langchain_dialed_host.py`
- `tests/cli/commands/test_verify_exit_codes.py`
- `tests/cli/commands/test_verify_integration.py`
- any further file a name search in steps 2–5 turns up

## Checks after every step

`run_pylint_check`, `run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`,
`run_mypy_check`, `run_lint_imports_check`, then `run_format_code` before the commit.
