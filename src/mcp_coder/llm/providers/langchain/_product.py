"""Product-specific user-facing texts of the LangChain model layer.

The only model-layer module a downstream copy (agent-workbench) replaces.
Keep every other model-layer module free of product names.
"""

INSTALL_HINT = "Install with: pip install 'mcp-coder[langchain]'"
OLLAMA_INSTALL_HINT = "Install with: pip install 'mcp-coder[langchain-ollama]'"
CONFIG_SECTION = "[llm.langchain]"
PRODUCT_NAME = "mcp-coder"
