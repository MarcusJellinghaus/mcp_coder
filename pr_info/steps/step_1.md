# Step 1: Project Configuration

**No tests required — pure configuration changes.**

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for full context.

Implement Step 1: add the required project configuration for LangChain support.
Make only the changes described below — do not add any source code yet.
Run lint-imports after editing .importlinter to verify the contract is valid.
```

---

## WHERE

| File | Action |
|---|---|
| `pyproject.toml` | Edit — three additions |
| `.importlinter` | Edit — one new contract appended at the end |

---

## WHAT

### `pyproject.toml` — three changes

**A. New optional extra** (after the existing `mlflow` extra):

```toml
# LangChain integration — alternative LLM providers (OpenAI, Gemini, …)
langchain = [
    "langchain-core>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-google-genai>=2.0.0",
]
```

**B. New pytest marker** (appended to `[tool.pytest.ini_options] markers`):

```toml
"langchain_integration: tests requiring LangChain and provider API access (network, auth needed)",
```

**C. Three new mypy overrides** (appended after the existing `mlflow` override):

```toml
[[tool.mypy.overrides]]
module = ["langchain_core", "langchain_core.*"]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["langchain_openai"]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["langchain_google_genai"]
ignore_missing_imports = true
```

---

### `.importlinter` — one new contract

Append after the `claude_sdk_isolation` contract:

```ini
# -----------------------------------------------------------------------------
# Contract: LangChain Library Isolation
# -----------------------------------------------------------------------------
# langchain_core, langchain_openai, langchain_google_genai are optional
# dependencies. Only the langchain provider package may import them.
# Same pattern as claude_sdk_isolation.
# -----------------------------------------------------------------------------
[importlinter:contract:langchain_library_isolation]
name = LangChain Library Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    langchain_core
    langchain_openai
    langchain_google_genai
ignore_imports =
    mcp_coder.llm.providers.langchain.** -> langchain_core
    mcp_coder.llm.providers.langchain.** -> langchain_openai
    mcp_coder.llm.providers.langchain.** -> langchain_google_genai
```

---

## HOW

- All changes are additive — no existing lines removed.
- The import-linter contract uses the **same structure** as `claude_sdk_isolation`
  directly above it. Copy and adapt.
- The mypy overrides follow the **same pattern** as the existing `mlflow` override.
- The pytest marker follows the **same format** as `mlflow_integration`.

---

## ALGORITHM

No runtime logic. Configuration only.

---

## DATA

No functions, no data structures.

---

## Verification

After editing, confirm:

1. `pyproject.toml` is valid TOML (no parse errors).
2. The `langchain` extra appears under `[project.optional-dependencies]`.
3. `langchain_integration` appears in the `markers` list.
4. Three `[[tool.mypy.overrides]]` blocks exist for the three langchain modules.
5. `.importlinter` contains `[importlinter:contract:langchain_library_isolation]`.
