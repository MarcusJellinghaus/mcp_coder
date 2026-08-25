# Step 5 — Per-backend contract validator (Azure rule included)

Declares what each field means per backend and validates it where a client is
built. The Azure-endpoint guard (Decision 6) is **one row of the table**, not a
separate function: `openai` + `api_version` ⇒ `base_url` required, resolved from
config **or** `AZURE_OPENAI_ENDPOINT`.

## WHERE

- **New:** `src/mcp_coder/llm/providers/langchain/_config_diagnostics.py`
- **New:** `tests/llm/providers/langchain/test_langchain_contract.py`
- Modified: `src/mcp_coder/llm/providers/langchain/__init__.py` —
  `_create_chat_model` only.

## WHAT

```python
Status = Literal["required", "optional", "ignored"]

_CONTRACT: dict[str, dict[str, Status]] = {
    "openai":    {"model": "required", "api_key": "required",
                  "base_url": "optional", "api_version": "optional"},
    "azure":     {"model": "required", "api_key": "required",
                  "base_url": "required", "api_version": "required"},
    "gemini":    {"model": "required", "api_key": "required",
                  "base_url": "ignored", "api_version": "ignored"},
    "anthropic": {"model": "required", "api_key": "required",
                  "base_url": "ignored", "api_version": "ignored"},
    "ollama":    {"model": "required", "api_key": "optional",
                  "base_url": "optional", "api_version": "ignored"},
}

_SUPPORTED_BACKENDS: tuple[str, ...] = ("openai", "gemini", "anthropic", "ollama")

# Keyed by *mode*, not by backend. Every variable that can satisfy the
# credential, verified against the installed SDKs (see HOW).
_API_KEY_ENV: dict[str, tuple[str, ...]] = {
    "openai":    ("OPENAI_API_KEY",),
    "azure":     ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_AD_TOKEN"),
    "gemini":    ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "ollama":    ("OLLAMA_API_KEY",),
}

# Modes that can build a working client with *no* credential at all, and the
# env var that signals it. Presence alone satisfies the rule — see HOW.
_KEYLESS_ENV: dict[str, str] = {"gemini": "GOOGLE_GENAI_USE_VERTEXAI"}


class Finding(TypedDict):
    key: str            # config field the finding is about
    ok: bool | None     # False = error, None = warning
    value: str          # human-readable message

def mode_of(config: Mapping[str, str | None]) -> str | None:
    """Return the contract mode, or None when the backend is not supported.

    'azure' for openai + api_version; otherwise the backend name itself, but
    only when it is one of _SUPPORTED_BACKENDS. 'azure' is an internal mode,
    not a configurable backend value, so a literal backend = "azure" returns
    None.
    """

def validate(config: Mapping[str, str | None]) -> list[Finding]:
    """Check config against the per-backend contract. Pure; never raises."""
```

## HOW

- `_create_chat_model` gains three lines **before** the backend dispatch, so all
  four provider paths (text, text-stream, agent, agent-stream) are covered by one
  site:
  ```python
  for finding in validate(config):
      if finding["ok"] is False:
          raise ValueError(finding["value"])
  ```
- The validator is pure and non-raising; `verify` (step 9) renders every finding.
- **Import direction (cycle guard).** `__init__.py` may import
  `from ._config_diagnostics import validate` at module level *only* because
  `_config_diagnostics` never imports the package `__init__` at module level.
  Step 6 adds `resolve_target()`, which needs `_create_chat_model` from
  `__init__` — that import **must be function-level** (see step 6). Keep
  `_config_diagnostics`'s module-level imports limited to stdlib and sibling
  private modules, or `import mcp_coder.llm.providers.langchain` breaks with a
  partially-initialised-module `ImportError`.
- **One key everywhere: the *mode*.** `_CONTRACT`, `_API_KEY_ENV` and
  `_is_present()` are all keyed by the value `mode_of()` returns — never by the
  raw `config["backend"]`. `_API_KEY_ENV` therefore carries an explicit
  `"azure"` row. Mixing the two namespaces would look up
  `_API_KEY_ENV["azure"]`, miss, and report a false `api_key` required-error for
  an Azure config whose key comes from `OPENAI_API_KEY` — which
  `_create_chat_model` would then raise on, breaking a working setup
  (Decision 6). (`_REDIRECT_ENV` in step 6 is the one table keyed by *backend*,
  because it describes SDK-level env redirects, not contract rules.)
- **`_API_KEY_ENV` rows are lists, because the SDKs read more than one
  variable.** The contract must accept *every* variable that actually produces
  credentials, or it turns a working setup into a false required-error — the
  same Decision-6 regression class as the mode/backend mix-up above. Measured in
  the project venv against the installed SDKs:
  - **azure** — `create_openai_model` passes `api_key=None` straight through to
    `openai.AzureOpenAI.__init__`, which falls back to `AZURE_OPENAI_API_KEY`,
    then `AZURE_OPENAI_AD_TOKEN`, and only then raises `OpenAIError: Missing
    credentials`. Both variables construct a client successfully with no config
    `api_key` and no `OPENAI_API_KEY`. (`OPENAI_API_KEY` stays in the row
    because `create_openai_model` reads it itself.)
  - **gemini** — `create_gemini_model` *omits* the `google_api_key` kwarg when
    neither config nor `GEMINI_API_KEY` yields a key, so langchain's
    `secret_from_env(["GOOGLE_API_KEY", "GEMINI_API_KEY"])` factory applies.
    `GOOGLE_API_KEY` is the SDK's *primary* variable and works on its own today.
- **`_KEYLESS_ENV`: the one credential-free carve-out, gemini/Vertex.** Measured:
  `ChatGoogleGenerativeAI` constructs with **no** credential when
  `GOOGLE_GENAI_USE_VERTEXAI` is truthy, and raises
  `ValidationError: API key required for Gemini Developer API` otherwise. The
  other keyless-sounding paths are unreachable through our code: `credentials`
  is a plain field with no env default and `create_gemini_model` never passes
  it, so ADC/`GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_CLOUD_PROJECT` do
  **not** rescue a keyless construction (both verified to still raise). So the
  rule is: gemini `api_key` is satisfied by config, `GEMINI_API_KEY`,
  `GOOGLE_API_KEY`, **or** a non-empty `GOOGLE_GENAI_USE_VERTEXAI`; otherwise
  `ok=False`, which is correct because construction is then certainly
  impossible — the same standard applied to `openai` below.
  **Presence, not truthiness.** `GOOGLE_GENAI_USE_VERTEXAI=0` / `=false` do not
  actually enable Vertex mode, so a presence test is over-permissive there. That
  direction is chosen deliberately: mirroring the SDK's truthiness parsing would
  risk a false required-error on a working setup (the failure this fix exists to
  remove), while over-permissiveness costs only a contract message the user
  still gets from the SDK — whose own text ("Provide api_key parameter or set
  GOOGLE_API_KEY/GEMINI_API_KEY environment variable") is already actionable,
  unlike the opaque OpenAI one.
- `api_key` presence means *config value, any of the mode's env vars, or its
  keyless carve-out* — check `config.get("api_key")`, then
  `any(os.environ.get(v) for v in _API_KEY_ENV[mode])`, then
  `os.environ.get(_KEYLESS_ENV.get(mode, ""), "")`.
- The `api_key` required-message names **all** of the mode's variables, so an
  Azure user reads `OPENAI_API_KEY`, `AZURE_OPENAI_API_KEY` or
  `AZURE_OPENAI_AD_TOKEN` rather than being pointed at one that may not be the
  one their setup uses.
- **`openai` `api_key` is unconditionally required — no `base_url` exception.**
  Decision 5 proposed an exit-neutral warning when `base_url` is set ("the relay
  may be unauthenticated"), but that is **contradicted by the installed SDK**:
  `create_openai_model` passes `api_key=None`, and langchain's
  `validate_environment` still builds `openai.AsyncOpenAI(api_key=None, ...)`
  unconditionally (only the *sync* client is skipped, by leaving `root_client`
  as `None`). `AsyncOpenAI.__init__` enforces credentials and raises
  `OpenAIError: Missing credentials. Please pass an api_key ... or set the
  OPENAI_API_KEY ... environment variable`. So a keyless `openai` config —
  `base_url` set or not — can never construct a client, and an `ok=None` warning
  would be exit-neutral advice for a setup that is certainly broken, followed by
  the opaque SDK error this issue exists to replace. The contract therefore
  raises `ok=False` for a missing `openai`/`azure` `api_key` in every case, and
  `_create_chat_model` fails with the actionable message instead.
  If an unauthenticated relay ever needs supporting, that is a *separate*
  change to `create_openai_model` (pass a placeholder key), not a softened
  contract.
- One conditional rule overrides the table:
  - **`azure` `base_url`** — satisfied by config `base_url` **or**
    `os.environ.get("AZURE_OPENAI_ENDPOINT")`. Consult the environment directly;
    an explicitly passed `None` bypasses langchain's `from_env` factory, so the
    langchain field is unreadable for this purpose.
- Unsupported backend (`mode_of()` returns `None`) → single `ok=False` finding on
  `key="backend"` listing the supported names (keeps the existing message
  wording). This includes a literal `backend = "azure"`: `azure` is an internal
  mode, so `verify` shows the unsupported-backend row (step 9) rather than
  `Backend [OK] azure`, and `_create_chat_model` keeps raising
  `Unsupported langchain backend: 'azure'`.

## ALGORITHM

```
mode_of(config):
    backend = config.get("backend")
    if backend == "openai" and config.get("api_version"): return "azure"
    return backend if backend in _SUPPORTED_BACKENDS else None   # "azure" → None

validate(config):
    mode = mode_of(config); findings = []
    if mode is None: return [error("backend", "Unsupported ... 'openai', ...")]
    for field, status in _CONTRACT[mode].items():
        present = _is_present(config, field, mode)        # mode-keyed; env-aware
                                                          # for api_key/base_url
        if status == "required" and not present:
            findings.append(_required_finding(mode, field))   # always ok=False
        elif status == "ignored" and config.get(field):
            findings.append(warn(field, f"{field} is ignored by backend '{mode}' — remove it"))
    return findings
```

## DATA

Example findings:

```python
[{"key": "base_url", "ok": False,
  "value": "api_version is set (Azure mode) but no base_url resolved from "
           "config or AZURE_OPENAI_ENDPOINT — set [llm.langchain] base_url to "
           "your Azure resource URL, or remove api_version for a non-Azure server"},
 {"key": "api_key", "ok": False,
  "value": "no api_key in [llm.langchain] and no OPENAI_API_KEY — set one; the "
           "OpenAI client cannot be built without credentials, even against a "
           "custom base_url"}]
```

The required-message enumerates the mode's whole `_API_KEY_ENV` row, so the
other two modes read:

```
azure : no api_key in [llm.langchain] and none of OPENAI_API_KEY,
        AZURE_OPENAI_API_KEY, AZURE_OPENAI_AD_TOKEN — set one
gemini: no api_key in [llm.langchain] and none of GEMINI_API_KEY,
        GOOGLE_API_KEY — set one (or GOOGLE_GENAI_USE_VERTEXAI for Vertex AI,
        which authenticates without a key)
```

## TDD

Table-driven tests, one per contract cell plus the conditionals:

1. `openai` plain, no `base_url`, no key/env → `api_key` `ok=False`.
2. `openai` **with** `base_url`, no key/env → `api_key` `ok=False` as well (no
   `base_url` exception), and the message names both `api_key` and
   `OPENAI_API_KEY`. Guard the SDK fact this rule rests on: with no key,
   `_create_chat_model` raises the contract `ValueError`, never the SDK's
   `OpenAIError: Missing credentials`.
3. `openai` + `api_version`, no `base_url`, no `AZURE_OPENAI_ENDPOINT` →
   `base_url` `ok=False`, message names `api_version` as the cause.
4. Same but `AZURE_OPENAI_ENDPOINT` set (monkeypatch) → **no** finding.
4b. Azure mode (`openai` + `api_version` + `base_url`) with **no** config
   `api_key` but `OPENAI_API_KEY` set (monkeypatch) → **no** `api_key` finding,
   and `_create_chat_model` does not raise (guards the mode-keyed
   `_API_KEY_ENV["azure"]` lookup).
4c. Same Azure config with **only** `AZURE_OPENAI_API_KEY` set, and again with
   **only** `AZURE_OPENAI_AD_TOKEN` — parametrised, all other credential vars
   cleared → **no** `api_key` finding in either case. Guard the SDK fact: assert
   `create_openai_model(model, None, base_url, api_version)` constructs without
   raising, so the widened row cannot silently drift from `AzureOpenAI`'s own
   fallback chain.
4d. Azure mode with **none** of the three set → `api_key` `ok=False`, and the
   message names all three variables.
5. `gemini` with `base_url` set → `ok=None` "ignored" warning; `api_version`
   likewise.
5b. `gemini` api_key sources, all other credential vars cleared:
   `GOOGLE_API_KEY` only → **no** `api_key` finding (assert
   `create_gemini_model(model, None)` constructs too); `GEMINI_API_KEY` only →
   no finding; `GOOGLE_GENAI_USE_VERTEXAI="1"` and nothing else → no finding
   (the keyless carve-out); **nothing** set → `api_key` `ok=False` and the
   message names `GEMINI_API_KEY` and `GOOGLE_API_KEY`.
6. `ollama` with only `model` → no findings.
7. Unsupported backend (`"opnai"`) → one `ok=False` finding on `backend`.
7b. Literal `backend = "azure"` → `mode_of()` returns `None` and the same
   `ok=False` `backend` finding is produced (the internal mode name is not a
   valid config value).
8. `_create_chat_model` raises `ValueError` on the Azure-missing case, and the
   message is the contract message, not the pydantic one.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`.
> Implement step 5: create
> `llm/providers/langchain/_config_diagnostics.py` with the `_CONTRACT` table,
> `mode_of()` and a pure, non-raising `validate()` returning `Finding` dicts
> (`ok=False` error, `ok=None` warning). Key `_CONTRACT`, `_API_KEY_ENV` and the
> presence check consistently by the **mode** (so `_API_KEY_ENV` needs an
> `"azure"` row — an Azure config keyed off `OPENAI_API_KEY` must not produce a
> required-error). `_API_KEY_ENV` values are **tuples**, listing every variable
> the SDKs actually accept: `azure` also honours `AZURE_OPENAI_API_KEY` and
> `AZURE_OPENAI_AD_TOKEN` (resolved by `openai.AzureOpenAI` itself, since
> `create_openai_model` passes `api_key=None` through), and `gemini` also
> honours `GOOGLE_API_KEY` (langchain's
> `secret_from_env(["GOOGLE_API_KEY", "GEMINI_API_KEY"])` factory applies
> whenever `create_gemini_model` omits the kwarg). Add `_KEYLESS_ENV =
> {"gemini": "GOOGLE_GENAI_USE_VERTEXAI"}`: a non-empty value satisfies gemini's
> `api_key` rule, because Vertex mode is the only path that constructs without a
> credential — test for *presence*, not truthiness. Failing to accept any of
> these turns a working setup into a false required-error, the Decision-6
> regression class. `mode_of()` returns `None` for any backend
> outside `_SUPPORTED_BACKENDS`, including the literal `"azure"`, which is an
> internal mode and not a valid config value. A missing `openai`/`azure`
> `api_key` is **always** an `ok=False` error — there is no `base_url`
> exception: langchain builds `openai.AsyncOpenAI(api_key=None)` regardless, and
> the SDK raises `OpenAIError: Missing credentials`, so a keyless config can
> never construct a client and must fail with the contract message instead.
> Include the one conditional rule: the Azure `base_url` rule that
> consults `AZURE_OPENAI_ENDPOINT` from the environment (not the langchain
> field). Call it from `_create_chat_model`, raising `ValueError` on the first
> error-level finding. Write table-driven tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
