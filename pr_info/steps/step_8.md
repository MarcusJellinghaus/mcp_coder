# Step 8 — Architecture documentation for the LangChain model layer

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_8.md`).
> Add a short section on the LangChain model layer to
> `docs/architecture/architecture.md`. Documentation only. Run format, then commit
> as one commit.

## WHERE

`docs/architecture/architecture.md`, section 5 "Building Block View": new
subsection `### LangChain model layer` after the block table, before the
"For module and function detail…" sentence.

## WHAT

Five short points, matching the document's terse style:

- **Modules:** the 15 model-layer modules in `src/mcp_coder/llm/providers/langchain/`
  (backends, `_models`, `_setup`, `_http`, `_exceptions`, `_errors_404`, `_usage`,
  `_preflight`, `_config_diagnostics`, `_messages`, `_provider_checks`, `_product`).
  The rest of the package (`__init__`, `agent`, `_mcp_tools`, `mcp_manager`,
  `approval_bridge`, `permission_bridge`, `verification`, `_config_source`) is
  mcp_coder glue: config loading, session storage, MCP.
- **Boundary:** from mcp_coder the layer imports only `llm.types`,
  `utils.config_hints`, `utils.log_utils`; the model layer receives its config as
  an argument (`_create_chat_model(config)`, `check_provider(config)`).
  Enforced by the two `langchain_model_layer*` contracts in `.importlinter`.
- **Product texts:** every product-specific user-facing text lives in `_product.py`.
- **Downstream copy:** agent-workbench copies the layer unchanged, replaces
  `_product.py`, and rewrites the `token_fingerprint` import to
  `mcp_coder_utils.redaction`.
- **Rule:** keep the layer self-contained; extracting it into a shared package
  later should be a move.

## HOW

Link `.importlinter` with the same relative-path style the section already uses
(`../../.importlinter`).

## ALGORITHM / DATA

None.
