# Step 7 — Import-linter contracts for the model layer

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_7.md`).
> Add the two forbidden contracts below to `.importlinter`, raise the
> import-linter floor in `pyproject.toml`, and make `run_lint_imports_check` pass.
> Do not loosen a contract to make it pass. Run pylint, pytest, mypy,
> lint-imports, format, then commit as one commit.

## WHERE

- `.importlinter` (new section after the LangChain isolation contracts)
- `pyproject.toml`: `"import-linter>=2.0"` → `"import-linter>=2.15"`

## WHAT

```ini
# -----------------------------------------------------------------------------
# Contract: LangChain Model Layer Self-Contained
# -----------------------------------------------------------------------------
# agent-workbench copies the LangChain model layer (backends, model setup,
# provider checks) unchanged and replaces only _product.py. The layer must stay
# self-contained: from mcp_coder it may import only llm.types, utils.config_hints
# and utils.log_utils. Wildcards cover packages added later. Glue and MCP
# modules of the langchain package are forbidden by name.
# -----------------------------------------------------------------------------
[importlinter:contract:langchain_model_layer]
name = LangChain Model Layer Self-Contained
type = forbidden
source_modules =
    mcp_coder.llm.providers.langchain.anthropic_backend
    mcp_coder.llm.providers.langchain.gemini_backend
    mcp_coder.llm.providers.langchain.ollama_backend
    mcp_coder.llm.providers.langchain.openai_backend
    mcp_coder.llm.providers.langchain._models
    mcp_coder.llm.providers.langchain._setup
    mcp_coder.llm.providers.langchain._http
    mcp_coder.llm.providers.langchain._exceptions
    mcp_coder.llm.providers.langchain._errors_404
    mcp_coder.llm.providers.langchain._usage
    mcp_coder.llm.providers.langchain._preflight
    mcp_coder.llm.providers.langchain._config_diagnostics
    mcp_coder.llm.providers.langchain._messages
    mcp_coder.llm.providers.langchain._provider_checks
    mcp_coder.llm.providers.langchain._product
forbidden_modules =
    mcp_coder.*
    mcp_coder.llm.*
    mcp_coder.llm.providers.*
    mcp_coder.llm.providers.langchain.agent
    mcp_coder.llm.providers.langchain._mcp_tools
    mcp_coder.llm.providers.langchain.mcp_manager
    mcp_coder.llm.providers.langchain.approval_bridge
    mcp_coder.llm.providers.langchain.permission_bridge
    mcp_coder.llm.providers.langchain.verification
    mcp_coder.llm.providers.langchain._config_source
    langchain_mcp_adapters
    langgraph
ignore_imports =
    mcp_coder.llm.providers.langchain._usage -> mcp_coder.llm.types
    mcp_coder.llm.providers.langchain._provider_checks -> mcp_coder.utils.config_hints
    mcp_coder.llm.providers.langchain._provider_checks -> mcp_coder.utils.log_utils

# -----------------------------------------------------------------------------
# Contract: LangChain Model Layer No Ancestor Imports
# -----------------------------------------------------------------------------
# Same boundary, for `from . import x` and imports from a parent __init__.
# With the default as_packages = True a forbidden ancestor of a source module
# is skipped silently, so the ancestors are pinned as single modules here.
# -----------------------------------------------------------------------------
[importlinter:contract:langchain_model_layer_ancestors]
name = LangChain Model Layer No Ancestor Imports
type = forbidden
as_packages = False
source_modules =
    (the same 15 modules)
forbidden_modules =
    mcp_coder
    mcp_coder.llm
    mcp_coder.llm.providers
    mcp_coder.llm.providers.langchain
```

## HOW

1. Before writing the `ignore_imports`, search the model-layer modules for every
   `mcp_coder.llm.types` import (module level, `TYPE_CHECKING` and lazy) and add
   one ignore line per importing module. An ignore line that matches no import is
   an error, so list only modules that really import it.
2. Check each forbidden module name is spelled exactly like the file on disk —
   a name missing from the graph is skipped silently (especially `_config_source`).
3. Run `run_lint_imports_check`. Both new contracts must be KEPT.
   - The ancestor contract passing confirms the lazy `from . import _models` in
     `_provider_checks` resolves to the submodule, not the package.
   - If a contract is broken by a real import from the model layer, remove that
     import at its source (it is a missed coupling), never by adding an ignore
     beyond the three allowed modules.
   - If lint-imports rejects the configuration itself (wildcards in
     `forbidden_modules` or `as_packages` unsupported by the installed version),
     write one line to `pr_info/.blocked.txt` and stop.
4. Sanity check the contract bites: temporarily add
   `from mcp_coder.utils import user_config` to `_messages.py`, confirm the
   allowlist contract breaks, then revert. Then temporarily add
   `from . import _resolve_session_id` (a name only the package `__init__`
   defines, so grimp records an import of `mcp_coder.llm.providers.langchain`)
   to `_messages.py` and confirm the ancestor contract breaks. Do not probe with
   `from . import <submodule>` (e.g. `_setup`): grimp resolves that to the
   submodule, so the ancestor contract stays KEPT. Revert both before committing.

## ALGORITHM

None — configuration.

## DATA

Two new KEPT contracts in the lint-imports report.
