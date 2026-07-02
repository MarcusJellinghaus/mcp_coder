# Summary — Improve OpenAI-compatible endpoint diagnostics (Issue #988)

## Goal

OpenAI (and custom OpenAI-compatible relays) already work via
`provider = "langchain"`, `backend = "openai"` (→ `langchain_openai.ChatOpenAI`).
A reporter hit `404 - {'detail': 'Not Found'}` because their configured
`endpoint` was a full request path (`…/vi/completions`) instead of the base URL.
`ChatOpenAI` **always** re-appends `/chat/completions` to `base_url`, so the
request doubled up → 404.

This is a **config mistake, not a bug**. Scope is **diagnostics / UX only**:
no new capability, no new dependency, no change to the LLM call path.

## Correct configuration (for reference)

```toml
[llm]
provider = "langchain"

[llm.langchain]
backend  = "openai"
model    = "llama3"
endpoint = "https://your-host/v1"   # base URL only — NO /chat/completions
api_key  = "..."                    # or OPENAI_API_KEY env var
# api_version must stay UNSET for generic OpenAI-compatible relays
```

## Architectural / design changes

There is **no architectural change**. No new modules, classes, or dependencies;
no change to control flow, provider dispatch, or the request path. The work adds
three small, self-contained diagnostic touch-points that reuse the existing
verify-style `{"ok": ..., "value": ...}` dict convention and the existing CLI
renderer contract:

1. **A pure, always-on string heuristic** (`_check_endpoint_shape`) added to the
   LangChain verification module. Zero network cost. It emits a verify-style row
   that the existing `_format_section` renderer already knows how to display.
   **It never contributes to `overall_ok`**, so it can never change the CLI exit
   code — hard pass/fail stays with the opt-in `--check-models` network probe.

2. **A wording improvement** in the existing `--check-models` probe path
   (`_list_models_for_backend`) so a live 404 reads as an endpoint/base-URL
   problem, distinct from auth and connection failures.

3. **A shared 404-hint helper** (`_format_404_hint`) in the LangChain provider
   package that de-duplicates the previously copy-pasted 404 block across
   `_ask_text` and `_ask_text_stream`, and adds a base-URL hint for the custom
   endpoint case (while skipping the wasted model-listing round-trip).

### Key design rules preserved from the issue

- **`/completions` → warning** (provably wrong 100% of the time — the client
  always re-appends `/chat/completions`).
- **Malformed URL → warning** (missing `http(s)://` scheme or no host).
- **Missing `/v1` → info only** (`/v1` is OpenAI's convention, not a client
  rule; relays may legitimately root elsewhere).
- **Gate the shape check on `api_version` being unset** — when set, the backend
  routes to `AzureChatOpenAI` with a bare `azure_endpoint`, so the base-URL
  heuristic would misfire.
- **The no-network heuristic never controls the exit code** (`overall_ok`
  untouched); only the opt-in `--check-models` probe can fail `verify`.

### Renderer contract (already in `cli/commands/verify.py`, unchanged)

`_format_section` maps `ok is True → [OK]`, `ok is False → [ERR]`, anything else
(`None`) → `[WARN]`. The actionable `-> hint` line renders **only** when
`ok is False`. Therefore a warning-level finding carries its guidance **inside
`value`**, and needs a `_LABEL_MAP` entry for a clean label. Info is rendered as
`ok=True` (`[OK]`) with an advisory note in `value`, since the renderer has no
dedicated info glyph.

## Files created / modified

No new folders or source files are created (all changes are edits). Planning
docs live under `pr_info/steps/`.

| File | Step | Change |
|------|------|--------|
| `src/mcp_coder/llm/providers/langchain/verification.py` | 1 | Add `_check_endpoint_shape`; wire into `verify_langchain` (openai only, excluded from `overall_ok`) |
| `src/mcp_coder/cli/commands/verify.py` | 1 | Add `_LABEL_MAP` entry `"endpoint_shape": "Endpoint"` |
| `src/mcp_coder/llm/providers/langchain/verification.py` | 2 | Reword 404 in `_list_models_for_backend` generic `except` as an endpoint/base-URL problem |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | 3 | Add `_format_404_hint`; call from `_ask_text` and `_ask_text_stream` (removes duplication) |
| `tests/llm/providers/langchain/test_langchain_verification.py` | 1, 2 | Unit tests for shape check + reworded 404 probe message |
| `tests/llm/providers/langchain/test_langchain_provider.py` | 3 | 404-hint tests for `_ask_text` |
| `tests/llm/providers/langchain/test_langchain_streaming.py` | 3 | 404-hint tests for `_ask_text_stream` |

## Step overview (one commit each)

- **Step 1 — Part A1:** always-on endpoint-shape heuristic in `verify`.
- **Step 2 — Part A2:** `--check-models` live-probe 404 messaging.
- **Step 3 — Part B:** shared prompt-path 404 hint helper.

Steps are independent and may be implemented in any order. Each step is
test-first and self-contained: tests + implementation + all three checks
(`run_pylint_check`, `run_pytest_check`, `run_mypy_check`) passing = one commit.

## Pytest invocation (fast unit subset)

```
run_pytest_check(extra_args=["-n", "auto", "-m",
  "not git_integration and not claude_cli_integration and not claude_api_integration "
  "and not formatter_integration and not github_integration and not langchain_integration"])
```
