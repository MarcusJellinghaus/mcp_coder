# Step 6 — Product-specific texts move to `_product.py`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_6.md`).
> Create `_product.py` with four constants holding today's exact values and make
> every model-layer module take its product-specific user-facing texts from it.
> Rendered texts must stay byte-identical: the existing exact-text tests are the
> guard and must pass **unchanged**. Run pylint, pytest, mypy, lint-imports,
> format, then commit as one commit.

## WHERE

- New: `src/mcp_coder/llm/providers/langchain/_product.py`
- Modified: `anthropic_backend.py`, `gemini_backend.py`, `ollama_backend.py`,
  `openai_backend.py`, `_models.py`, `_preflight.py`, `_config_diagnostics.py`,
  `_errors_404.py`, `_provider_checks.py`

## WHAT

```python
"""Product-specific user-facing texts of the LangChain model layer.

The only model-layer module a downstream copy (agent-workbench) replaces.
Keep every other model-layer module free of product names.
"""

INSTALL_HINT = "Install with: pip install 'mcp-coder[langchain]'"
OLLAMA_INSTALL_HINT = "Install with: pip install 'mcp-coder[langchain-ollama]'"
CONFIG_SECTION = "[llm.langchain]"
PRODUCT_NAME = "mcp-coder"
```
Plain literals; no constant is built from another.

## HOW

Replace each literal with the constant inside the existing string, e.g.
`"LangChain OpenAI backend requires extra dependencies.\n" f"{INSTALL_HINT}"`.
Import with `from ._product import INSTALL_HINT` etc. In the four backends the
import goes **above** the `try:` that imports the langchain package.

| Module | Place | Constant |
|---|---|---|
| 4 backends | `ImportError` message | `INSTALL_HINT` |
| `_models.py` | the `list_*` `ImportError` messages (4–5 places) | `INSTALL_HINT` |
| `_preflight._ollama_preflight` | `ImportError` message | `OLLAMA_INSTALL_HINT` |
| `_config_diagnostics._required_finding` | 3 messages naming `[llm.langchain]` | `CONFIG_SECTION` |
| `_config_diagnostics._source_for` | `"config.toml [llm.langchain] base_url"` | `CONFIG_SECTION` |
| `_provider_checks.check_provider` | `api_key_override` row | `CONFIG_SECTION` |
| `_errors_404._format_404_hint` | "mcp-coder appends /chat/completions" | `PRODUCT_NAME` |
| `_provider_checks._check_base_url_shape` | "(mcp-coder appends /chat/completions)" | `PRODUCT_NAME` |
| `_provider_checks._list_models_for_backend` | "(mcp-coder appends /chat/completions)" | `PRODUCT_NAME` |

Docstrings and comments may keep naming mcp-coder. `config.toml` stays literal
(not in the issue's scope).

Acceptance search after the edit: search string literals of every model-layer
module except `_product.py` for `mcp-coder`, `mcp_coder` and `[llm.langchain]`.
Only docstring / comment hits may remain. Fix any literal hit.

## ALGORITHM

None — literal substitution.

## DATA

Four `str` constants. No new tests: the exact-text tests (coverage_gaps,
ollama_agent, provider, effective_config, verify_sections_config, resolve_target,
404_hints, verification, contract_rows, base_url_shape) already pin every
rendered string and must pass without edits.
