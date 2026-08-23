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

_API_KEY_ENV: dict[str, str] = {          # reuse verification._BACKEND_ENV_VARS values
    "openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY", "ollama": "OLLAMA_API_KEY",
}

class Finding(TypedDict):
    key: str            # config field the finding is about
    ok: bool | None     # False = error, None = warning
    value: str          # human-readable message

def mode_of(config: Mapping[str, str | None]) -> str:
    """Return the contract mode: 'azure' for openai+api_version, else the backend."""

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
- `api_key` presence means *config value or the backend env var* — check
  `config.get("api_key") or os.environ.get(_API_KEY_ENV[backend])`.
- Two conditional rules override the table:
  - **`openai` `api_key`** — error only when `base_url` is unset (public OpenAI);
    when `base_url` is set the server may be unauthenticated, so missing is
    `ok=None` (Decision 5).
  - **`azure` `base_url`** — satisfied by config `base_url` **or**
    `os.environ.get("AZURE_OPENAI_ENDPOINT")`. Consult the environment directly;
    an explicitly passed `None` bypasses langchain's `from_env` factory, so the
    langchain field is unreadable for this purpose.
- Unknown backend → single `ok=False` finding on `key="backend"` listing the
  supported names (keeps the existing message wording).

## ALGORITHM

```
validate(config):
    mode = mode_of(config); findings = []
    if mode not in _CONTRACT: return [error("backend", "Unsupported ... 'openai', ...")]
    for field, status in _CONTRACT[mode].items():
        present = _is_present(config, field, mode)        # env-aware for api_key/base_url
        if status == "required" and not present:
            findings.append(_required_finding(mode, field))   # ok=False, or None for openai api_key+base_url
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
 {"key": "api_key", "ok": None,
  "value": "no api_key and no OPENAI_API_KEY — fine if the server at base_url "
           "is unauthenticated"}]
```

## TDD

Table-driven tests, one per contract cell plus the conditionals:

1. `openai` plain, no `base_url`, no key/env → `api_key` `ok=False`.
2. `openai` with `base_url`, no key/env → `api_key` `ok=None` (exit-neutral).
3. `openai` + `api_version`, no `base_url`, no `AZURE_OPENAI_ENDPOINT` →
   `base_url` `ok=False`, message names `api_version` as the cause.
4. Same but `AZURE_OPENAI_ENDPOINT` set (monkeypatch) → **no** finding.
5. `gemini` with `base_url` set → `ok=None` "ignored" warning; `api_version`
   likewise.
6. `ollama` with only `model` → no findings.
7. Unknown backend → one `ok=False` finding on `backend`.
8. `_create_chat_model` raises `ValueError` on the Azure-missing case, and the
   message is the contract message, not the pydantic one.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`.
> Implement step 5: create
> `llm/providers/langchain/_config_diagnostics.py` with the `_CONTRACT` table,
> `mode_of()` and a pure, non-raising `validate()` returning `Finding` dicts
> (`ok=False` error, `ok=None` warning). Include the two conditional rules: the
> `openai` `api_key` rule keyed on `base_url`, and the Azure `base_url` rule that
> consults `AZURE_OPENAI_ENDPOINT` from the environment (not the langchain
> field). Call it from `_create_chat_model`, raising `ValueError` on the first
> error-level finding. Write table-driven tests first (TDD).
> Use MCP tools only. Run pytest (fast markers), pylint and mypy; all must pass.
