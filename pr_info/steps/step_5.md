# Step 5: Documentation

Update two existing documentation files.
No code changes, no tests.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for full context.
Steps 1–4 are already complete and all tests pass.

Implement Step 5: update the two documentation files as described below.
Read each file in full before editing so you preserve its existing structure
and formatting conventions.
```

---

## WHERE

| File | Action |
|---|---|
| `docs/configuration/config.md` | Edit — add `[llm]` section documentation |
| `docs/architecture/architecture.md` | Edit — update LLM provider section |

---

## WHAT & HOW

### `docs/configuration/config.md`

**1. Add a row to the Quick Reference table:**

```markdown
| **LLM Provider** | `[llm]` section in `config.toml` |
```

**2. Add a new top-level section `### [llm]`** after the existing `### [coordinator]`
section and before `### [jenkins]`:

````markdown
### [llm]

Selects the LLM provider. Defaults to `"claude"` when omitted.

| Field | Type | Description | Required | Default |
|-------|------|-------------|----------|---------|
| `provider` | string | LLM provider: `"claude"` or `"langchain"` | No | `"claude"` |

**Example — use Claude (default, no change needed):**
```toml
[llm]
provider = "claude"
```

**Example — use LangChain:**
```toml
[llm]
provider = "langchain"
```

### [llm.langchain]

LangChain backend configuration. Required when `[llm] provider = "langchain"`.

Install the extra dependency first:
```bash
pip install 'mcp-coder[langchain]'
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `backend` | string | LangChain backend: `"openai"` or `"gemini"` | Yes |
| `model` | string | Model name (e.g. `"gpt-4o"`, `"gemini-1.5-pro"`) | Yes |
| `api_key` | string | API key (env var takes priority — see below) | No |
| `endpoint` | string | Custom base URL (e.g. Azure, Ollama). Mapped to LangChain's `base_url` | No |

**Example — OpenAI GPT-4o:**
```toml
[llm]
provider = "langchain"

[llm.langchain]
backend  = "openai"
model    = "gpt-4o"
api_key  = "sk-..."       # or set OPENAI_API_KEY env var
```

**Example — Google Gemini:**
```toml
[llm]
provider = "langchain"

[llm.langchain]
backend  = "gemini"
model    = "gemini-1.5-pro"
api_key  = "..."          # or set GEMINI_API_KEY env var
```

**Example — Azure OpenAI (custom endpoint):**
```toml
[llm]
provider = "langchain"

[llm.langchain]
backend  = "openai"
model    = "gpt-4o"
endpoint = "https://my-resource.openai.azure.com/"
api_key  = "..."
```

**Example — Local Ollama:**
```toml
[llm]
provider = "langchain"

[llm.langchain]
backend  = "openai"       # Ollama is OpenAI-compatible
model    = "llama3"
endpoint = "http://localhost:11434/v1"
```

#### Environment Variable Overrides

Environment variables take **highest priority** over config file values.

| Environment Variable | Overrides | Backend |
|---------------------|-----------|---------|
| `OPENAI_API_KEY` | `[llm.langchain] api_key` | `openai` |
| `GEMINI_API_KEY` | `[llm.langchain] api_key` | `gemini` |

**Usage in CI/CD:**
```bash
export OPENAI_API_KEY="sk-prod-key"
mcp-coder prompt "Summarise this PR"
```

#### Session Continuity

LangChain conversations are **resumed automatically** using the same
`session_id` mechanism as Claude. Conversation history is stored locally at:

- **Windows:** `%USERPROFILE%\.mcp_coder\sessions\langchain\{session_id}.json`
- **Linux/macOS:** `~/.mcp_coder/sessions/langchain/{session_id}.json`

This means sessions survive process restarts, unlike Claude (which stores
history server-side).
````

---

### `docs/architecture/architecture.md`

**1. Update the LLM System table** in Section 5 (Building Block View).

Find the `- **Providers**: llm/providers/` bullet and expand it:

```markdown
- **Providers**: `llm/providers/` - Provider implementations
  - `claude/` - Claude Code CLI/API integration (tests: `llm/providers/claude/test_*.py`)
    - `claude_code_cli.py` - Claude Code CLI integration with stream-json session logging
    - `claude_code_api.py` - Claude Code API integration
    - `logging_utils.py` - Logging utilities for LLM requests/responses/errors
  - `langchain/` - LangChain multi-backend integration (tests: `llm/providers/langchain/test_*.py`)
    - `__init__.py` - Entry point `ask_langchain()`, config loading, backend dispatch
    - `openai.py` - OpenAI / Azure / Ollama backend via `ChatOpenAI`
    - `gemini.py` - Google Gemini backend via `ChatGoogleGenerativeAI`
    - **Optional install**: `pip install 'mcp-coder[langchain]'`
    - **Session storage**: history persisted to `~/.mcp_coder/sessions/langchain/`
```

**2. Update the LLM session storage description** in the Storage subsection:

Add after the existing `session_storage.py` description:

```markdown
  - **LangChain session history**: `store_langchain_history()` / `load_langchain_history()`
    in `session_storage.py` persist message lists as JSON to
    `~/.mcp_coder/sessions/langchain/{session_id}.json`.
    Unlike Claude (server-side history), LangChain history is managed by mcp-coder locally.
```

**3. Update Section 8 (Cross-cutting Concepts) — Testing Strategy markers table:**

Add `langchain_integration` to the markers list:

```markdown
  - `langchain_integration`: LangChain API tests (network, auth needed)
    in `llm/providers/langchain/test_*.py`
    - **When to use**: Testing LangChain provider integrations, real API calls
    - **Requirements**: LangChain packages installed, API keys configured
```

**4. Update the Key Features list** in Section 1 (Introduction) if it references
Claude specifically:

```markdown
- **LLM Integration**: Multi-provider interface with Claude Code CLI/API support
  and optional LangChain backends (OpenAI, Gemini, and others)
```

---

## DATA

No functions, no return values — documentation only.

---

## Verification

After editing:

1. Both markdown files render without broken links or table formatting errors.
2. The `[llm]` section in `config.md` follows the same table format as `[jenkins]`.
3. The `langchain/` provider entry in `architecture.md` is parallel in structure
   to the existing `claude/` entry.
4. All four `endpoint` examples in `config.md` are copy-pasteable as valid TOML.
