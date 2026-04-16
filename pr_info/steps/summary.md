# Summary — Issue #829: Optional extras reorganisation + langchain isolation

## Goal

Split the monolithic `[langchain]` extra into layered per-provider extras, move
`mcp_manager.py` under the `providers/langchain/` namespace, tighten
import-linter coverage for four transitive langchain libraries, and document
the new extras layout.

## Architectural / Design Changes

### 1. Packaging topology (`pyproject.toml`)

**Before** — flat extras:

```
[langchain]  = core + 3 provider wrappers + mcp-adapters + langgraph + httpx
[truststore] = truststore               (standalone)
[mcp]        = ()                        (empty — leftover)
```

**After** — layered extras:

```
[langchain-base]      = langchain-core, langchain-mcp-adapters, langgraph,
                        httpx, truststore
[langchain-openai]    = [langchain-base] + langchain-openai
[langchain-gemini]    = [langchain-base] + langchain-google-genai
[langchain-anthropic] = [langchain-base] + langchain-anthropic
[langchain-ollama]    = [langchain-base] + langchain-ollama
[langchain]           = meta: all four per-provider extras
```

`[truststore]` merges into `[langchain-base]` (only exercised alongside
langchain HTTP/SSL plumbing). `[mcp]` is dropped (empty leftover).
`[dev]` now aggregates `types,test,langchain,mlflow,tui` (drops `mcp`).

**Key property:** `pip install mcp-coder[langchain]` installs the identical
package set as today — zero breaking change for existing users. Power users
opt into smaller footprints (e.g. `[langchain-anthropic]` avoids `grpcio`,
`protobuf`, `tiktoken`).

### 2. Module relocation

`src/mcp_coder/llm/mcp_manager.py` → `src/mcp_coder/llm/providers/langchain/mcp_manager.py`.

The module is only instantiated on the langchain code path
(`cli/commands/icoder.py:84`), and already imports `_sanitize_tool_schema`
from `providers.langchain.agent` at module top level — a pre-existing layering
leak. After the move, the import is intra-package and the langchain isolation
contract applies naturally.

### 3. New import-linter contract

A single grouped `forbidden` contract `langchain_transitive_isolation`
covering `langchain_mcp_adapters`, `langgraph`, `truststore`, `httpx` —
mirroring the existing `langchain_library_isolation` pattern (same
`source_modules = mcp_coder`, same dual-form `ignore_imports` for
`providers.langchain` and `providers.langchain.**`).

### 4. Documentation

New `docs/configuration/optional-dependencies.md` with a table mapping each
extra to what it enables and when to install it. Includes the name mismatch
note (`[langchain-gemini]` wraps PyPI `langchain-google-genai`). README gains
a short "Optional features" subsection under `### Installation` pointing to
this page. The three existing docs that already mention install hints
(`docs/configuration/config.md`, `docs/configuration/mlflow-integration.md`,
`docs/architecture/architecture.md`) each gain a one-line pointer to the
new reference page.

## Out of Scope (tracked separately)

- Ollama backend code — #727 (this PR only adds the installable extra slot)
- MLflow reorg + isolation contract — #837
- Top-level-import discipline / `deptry` / minimal-install CI smoke — #838

## Files & Folders — Created / Modified / Deleted

### Created
- `src/mcp_coder/llm/providers/langchain/mcp_manager.py` *(moved from `llm/`)*
- `docs/configuration/optional-dependencies.md`

### Modified
- `pyproject.toml` — extras restructure, `[dev]` update
- `.importlinter` — new `langchain_transitive_isolation` contract
- `README.md` — Optional features pointer
- `docs/configuration/config.md` — one-line pointer to the new page near the `[langchain]` install hint
- `docs/configuration/mlflow-integration.md` — one-line pointer to the new page near the install hint
- `docs/architecture/architecture.md` — one-line pointer to the new page near the `langchain/` optional-install bullet
- `src/mcp_coder/cli/commands/icoder.py` — import path update
- `src/mcp_coder/icoder/services/llm_service.py` — TYPE_CHECKING import
- `src/mcp_coder/icoder/core/commands/info.py` — TYPE_CHECKING import
- `tests/llm/test_mcp_manager.py` — import path update
- `tests/icoder/test_info_command.py` — import path update

### Deleted
- `src/mcp_coder/llm/mcp_manager.py` *(moved — old location)*

## Step Sequence

The issue mandates this order because step 3's contract is only valid after
step 1's move.

1. **step_1.md** — Move `mcp_manager.py` under `providers/langchain/`
2. **step_2.md** — Restructure `pyproject.toml` extras
3. **step_3.md** — Add `langchain_transitive_isolation` import-linter contract
4. **step_4.md** — Documentation (new page + pointers from README and the three existing install-hint docs)

Each step = one commit; all three code-quality checks (pylint, pytest,
mypy) plus `lint-imports` green at the end of each step.

## Acceptance

- `pip install mcp-coder[langchain]` identical package set to current (verified
  by `pip list` diff in PR description)
- `pip install mcp-coder[langchain-anthropic]` in clean venv installs only
  base + anthropic wrapper (no `openai`, `google-genai`, `grpcio`, `tiktoken`)
- `lint-imports` passes with the new contract enabled
- `docs/configuration/optional-dependencies.md` exists, linked from README
  and from `docs/configuration/config.md`,
  `docs/configuration/mlflow-integration.md`, and
  `docs/architecture/architecture.md`
- All existing tests pass
