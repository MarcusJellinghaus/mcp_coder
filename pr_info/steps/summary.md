# Issue #1117 — LangChain config/verify diagnosability

**Goal:** kill the implicit-routing footgun in the langchain provider and make
`mcp-coder verify` report what the client will *actually* do.

Two deliverables:

1. **Config clarity** — `endpoint` becomes `base_url` (hard break, no alias), and
   config is validated against an explicit **per-backend contract** at the point a
   client is built. Azure stays an explicit *mode* of the `openai` backend.
2. **Verify diagnosability** — the resolved target is read from the *constructed
   client*, not computed from config; every silent redirect (`OPENAI_BASE_URL`,
   `OLLAMA_HOST`, `OPENAI_API_KEY`, `MCP_CODER_LLM_PROVIDER`) is surfaced; the
   test prompt carries the real message shape.

---

## Architectural / design changes

### 1. Backend selection becomes declarative

Today the client class is chosen by a side-effect: `if api_version:` in
`openai_backend.py:43` routes to `AzureChatOpenAI`, and the single `endpoint`
key means `azure_endpoint` on one branch and `base_url` on the other.

After this change the *routing stays the same* (Azure is still a mode of
`openai` — it ships in the same `langchain_openai` package and reuses
`OPENAI_API_KEY`), but the consequences of that routing are **declared in a
table** rather than discovered by the user at runtime:

| backend / mode | required | optional | ignored (warn) |
|---|---|---|---|
| `openai` (plain) | `model`, `api_key`¹ | `base_url` | — |
| `openai` + `api_version` (Azure) | `model`, `api_key`¹, `base_url`² | — | — |
| `gemini` | `model`, `api_key`¹ | — | `base_url`, `api_version` |
| `anthropic` | `model`, `api_key`¹ | — | `base_url`, `api_version` |
| `ollama` | `model` | `base_url`, `api_key` | `api_version` |

¹ or the backend env var. For `openai` this is *conditional*: an error only when
`base_url` is unset (public OpenAI, where the diagnosis is certain); an
exit-neutral warning when `base_url` is set (the relay may be unauthenticated).
² checked on the **resolved** value — config `base_url` **or**
`AZURE_OPENAI_ENDPOINT`.

The Azure-endpoint guard is **not a separate function**: it is one row of this
table. One rule, one message, one code path.

### 2. Truth is read from the client, never computed from config

Measured behaviour of the installed SDK: `ChatOpenAI(base_url=None)` leaves the
langchain field `None` while the underlying `openai` SDK dials `OPENAI_BASE_URL`
if set, else `https://api.openai.com/v1/`. Any "resolved base_url" derived from
config alone is therefore *wrong* whenever that env var is set.

New primitive: `resolve_target(config) -> ResolvedTarget(url, source, verified)`.
It constructs the chat model (local, no network), reads
`root_client.base_url` (openai/azure) or `ChatOllama.base_url`, closes the httpx
clients, and falls back to the config value **labelled unverified** when
construction fails. `gemini`/`anthropic` return an explicit `n/a`.

Three consumers share it: the effective-config echo, the rebased base-URL shape
check, and the connection-error message.

**One call per `verify` run.** `verify_langchain` — which already loads the
config and resolves the api key — makes the single `resolve_target(config)` call
and binds it to a local, then hands it to `describe_effective_config()` (step 7)
and `_check_base_url_shape()` (step 8). `_config_diagnostics` must import
`_create_chat_model` **inside** `resolve_target` (function-level): step 5 has the
package `__init__` importing `validate` from `_config_diagnostics`, so a
module-level import back would be a cycle and break
`import mcp_coder.llm.providers.langchain`.

### 3. Validation is pure, non-raising and shared

`validate(config) -> list[Finding]` is a pure function. `_create_chat_model`
raises on the first error-level finding (one site, reaching all four provider
paths); `verify` renders *every* finding and wraps construction in try/except.
`_load_langchain_config` stays raise-free — it runs on every `verify`, including
for claude users who have never configured langchain.

### 4. No new vocabulary where the codebase already has one

Findings reuse the existing verify entry shape `{"ok": True|False|None, "value": str}`
(`ok=None` = warning), which `_format_section` already renders and
`_compute_exit_code` already ignores except through `overall_ok`. Consequence:
**no new finding type, no new renderer, no change to `verify_exit_code.py`** for
the contract, and the naive `model` / `api_key` rows in `verify_langchain` are
*replaced* by contract findings rather than running beside them.

### 5. The effective-config echo is a non-dict entry

`_format_section` reads `ok`/`value` from every **dict-valued** entry, so an echo
sub-block would render as a warning row with an empty value — but it `continue`s
past anything that is not a dict (`verify_formatting.py:190-191`), and
`_collect_install_hints` has the same guard. So `describe_effective_config()`
returns `list[tuple[str, str]]`, `verify_langchain` stores it as the list-valued
`result["effective_config"]`, and `verify.py` prints it with
`_format_row(label, "", value, indent=2)` — an empty marker already renders
without a status symbol (as `_print_environment_section` does today). Nothing in
the formatter or the exit-code path can see it, so "rendered without status
symbols and excluded from exit-code logic" is structural, not a workaround.
Carrying it in the result dict also keeps `verify.py` out of the private
llm-layer helpers (`_load_langchain_config`, `_resolve_api_key`) and avoids a
second config load per run. *(This takes the alternative the issue's Constraints
section offers — keep the echo out of `_format_section`'s reach — over
Decision 11's `{ok,value}` sub-block wording.)*

### 6. Explicit arguments beat the environment

`prompt_llm` / `prompt_llm_stream` currently re-apply `MCP_CODER_LLM_PROVIDER`
over the `provider=` they were handed, so `verify --llm-method langchain` can
report one provider and test another. Both signatures become
`provider: str | None = None` and resolve `explicit or env or "claude"`.

The config tier (`[llm] default_provider`) stays where it already is — in
`resolve_llm_method` at the CLI layer, which every entry point calls before
`prompt_llm`. End-to-end precedence is therefore **explicit > env > config**
without duplicating resolution logic or adding an `llm → cli` import.

### 7. Source provenance needs no new resolver

Only two fields need a *source*: `api_key` (already returned by
`_resolve_api_key`) and `base_url` (returned by `resolve_target`). `backend` and
`model` need values; `mode` is derived from `api_version`. So
`_load_langchain_config`'s flat `dict[str, str | None]` return shape is untouched.

`_resolve_api_key` does gain a third return element, `overridden: bool` (step 7):
today it reports only the *winning* source, so an `OPENAI_API_KEY` that beats a
configured `api_key` is indistinguishable from one that filled a gap — and the
acceptance criterion asks for exactly that distinction. One in-repo caller
(`verify_langchain`) plus its tests.

### 8. Module boundaries

`verify.py` (675), `langchain/verification.py` (518) and `utils/user_config.py`
(721) are all over the 400-line soft limit, so new logic lands in **two** new
modules:

- `utils/config_hints.py` — per-section rename table + a `difflib` near-miss
  helper, reused by both the unknown-key path and the `--check-models` cross-check.
- `llm/providers/langchain/_config_diagnostics.py` — the backend contract table,
  the redirect-env table, `validate()`, `resolve_target()`,
  `describe_effective_config()`. One cohesive module answering *"what will this
  config actually do?"*.

---

## Files created

| Path | Purpose |
|---|---|
| `src/mcp_coder/utils/config_hints.py` | rename table `(section, key) -> hint`, `suggest()` near-miss helper |
| `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py` | contract table, redirect table, `validate()`, `resolve_target()`, `describe_effective_config()`, `dialed_url()` |
| `tests/utils/test_config_hints.py` | unit tests for the above |
| `tests/llm/providers/langchain/test_langchain_contract.py` | contract validator tests |
| `tests/llm/providers/langchain/test_langchain_resolve_target.py` | probe / echo tests |

## Files modified

**Source**

| Path | Steps |
|---|---|
| `src/mcp_coder/utils/user_config.py` | 1 (schema + env var), 2 (unknown-key hints), 18 (smart-quote hint) |
| `src/mcp_coder/llm/providers/langchain/__init__.py` | 1, 4 (raise-free loader), 5 (validator call), 10 (dialed host) |
| `src/mcp_coder/llm/providers/langchain/openai_backend.py` | 1 |
| `src/mcp_coder/llm/providers/langchain/ollama_backend.py` | 1 |
| `src/mcp_coder/llm/providers/langchain/_models.py` | 1 |
| `src/mcp_coder/llm/providers/langchain/_preflight.py` | 1 |
| `src/mcp_coder/llm/providers/langchain/_errors_404.py` | 1 |
| `src/mcp_coder/llm/providers/langchain/_exceptions.py` | 1 (`base_url_hint`) |
| `src/mcp_coder/llm/providers/langchain/verification.py` | 1, 7 (single `resolve_target` call, echo rows, redirect + api_key-override rows, `_resolve_api_key` 3-tuple), 8 (shape rebase + `base_url_shape` key), 9 (contract rows), 10, 11 (model cross-check) |
| `src/mcp_coder/cli/commands/verify_formatting.py` | 7 (`base_url_redirect`, `api_key_override` labels), 8 (`base_url_shape` / "Base URL"), 9 + 11 (label map entries) |
| `src/mcp_coder/cli/commands/verify.py` | 3, 7, 13, 14, 16, 17 |
| `src/mcp_coder/cli/commands/verify_exit_code.py` | 16 (`prompts_ok` param) |
| `src/mcp_coder/llm/interface.py` | 12 (provider precedence) |
| `src/mcp_coder/prompts/prompt_loader.py` | 15 (`_resolve_path`, runtime WARNING) |

**Docs**

| Path | Steps |
|---|---|
| `docs/configuration/config.md` | 19 |
| `docs/architecture/architecture.md` | 19 (new module in the langchain list) |

**Tests** — step 1 touches ~22 existing test files (`_make_config()` helpers and
`endpoint=` kwargs); later steps touch
`tests/llm/test_interface.py`, `tests/utils/test_user_config*.py`,
`tests/cli/commands/test_verify*.py`,
`tests/llm/providers/langchain/test_langchain_verification*.py`,
`tests/prompts/`.

---

## Steps

| # | Step | Theme |
|---|---|---|
| 1 | `endpoint` → `base_url` rename (config key, env var, signatures, hints) | config clarity |
| 2 | Unknown-key hints (rename + did-you-mean) | config clarity |
| 3 | Retired env-var warning in `verify` | config clarity |
| 4 | `_load_langchain_config` never raises | prerequisite |
| 5 | Per-backend contract validator (incl. Azure rule) | contract |
| 6 | `resolve_target()` probe | truth from client |
| 7 | Effective-config echo + redirect flag + api_key-override flag | verify |
| 8 | Base-URL shape check rebased on the resolved target (+ `base_url_shape` key/label, split from step 1) | verify |
| 9 | Contract findings + exit-code wiring | verify |
| 10 | Connection errors name the dialed host | errors |
| 11 | `--check-models` model cross-check | verify |
| 12 | `prompt_llm` / `prompt_llm_stream` precedence | provider selection |
| 13 | Test prompt passes `project_dir=` | verify |
| 14 | `MCP_CODER_LLM_PROVIDER` source visibility | verify |
| 15 | Prompt path resolver + runtime WARNING | prompts |
| 16 | PROMPTS section: lengths, source, missing → error | verify |
| 17 | TLS / proxy summary line | verify |
| 18 | Smart-quote hint in `_format_toml_error` | config |
| 19 | Documentation | docs |

Ordering constraints: **1 before 2** (the `endpoint` rename hint is untestable
until step 1 removes `endpoint` from the schema — before that it is a *known*
key and never reaches the unknown-key branch); **1 before 3** (step 3's
"retired env var is set and ignored" message is false until step 1 stops
reading `MCP_CODER_LLM_LANGCHAIN_ENDPOINT`); 4 before 5; 5 before 6 (same
module, and 6's deferred import exists because of 5's wiring); 5 before 9;
6 before 7, 8 and 10; 7 before 8 (7 introduces the single `resolve_target` call
that 8 reuses); **7 before 9** (9 unpacks the 3-tuple
`key, src, _over = _resolve_api_key(...)` that 7 introduces, so 9 does not
compile against the step-6 tree); 2 before 11 (`suggest()`); 12 before 13;
15 before 16 (`is_prompt_configured_but_missing`). Steps 14, 17 and 18 are
independent; 19 (docs) is last because it describes the finished behaviour.

## Conventions for every step

- **TDD**: write the failing test first, then the implementation.
- **One commit per step**: tests + implementation + all three checks green.
- Use MCP tools only (`mcp__workspace__*`, `mcp__tools-py__*`).
- Fast test run:
  `mcp__tools-py__run_pytest_check(extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration and not llm_integration and not textual_integration"])`
- Then `mcp__tools-py__run_pylint_check` and `mcp__tools-py__run_mypy_check`.
