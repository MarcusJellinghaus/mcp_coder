# Step 5 — Split `verification.py`: provider checks move to `_provider_checks.py`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`).
> Write `test_langchain_provider_checks.py` and retarget existing test patches
> first, then create `_provider_checks.py` and slim down `verification.py`.
> The step-1 test `test_langchain_verify_row_order.py` must pass **unchanged**.
> No re-exports of moved names from `verification`. Run pylint, pytest, mypy,
> lint-imports, format, then commit as one commit.

## WHERE

- New: `src/mcp_coder/llm/providers/langchain/_provider_checks.py`
- New: `tests/llm/providers/langchain/test_langchain_provider_checks.py`
- Modified: `verification.py`, `src/mcp_coder/cli/commands/verify_sections.py`
- Tests retargeted (at least): `test_langchain_verification.py`,
  `test_langchain_verification_ollama.py`, `test_langchain_effective_config.py`,
  `test_langchain_contract_rows.py`, `test_langchain_base_url_shape.py`,
  `test_langchain_dialed_host.py`, `tests/cli/commands/test_verify_exit_codes.py`,
  `tests/cli/commands/test_verify_integration.py`

## WHAT

`_provider_checks.py` (model layer) — moved verbatim from `verification.py`:
`_BACKEND_PACKAGES`, `_mask_api_key`, `_resolve_api_key`, `_row_from`,
`_api_key_default_value`, `_check_package_installed`, `_check_base_url_shape`,
`_check_model_listed`, `_list_models_for_backend`, plus the new entry point:

```python
def check_provider(config: Mapping[str, str | None], check_models: bool = False) -> dict[str, Any]:
    """Every verify_langchain row except the MCP rows, plus overall_ok over them."""
```

Imports: `importlib.util`, `os`, `Mapping`, `Any`, `urlparse`,
`from mcp_coder.utils.config_hints import suggest`,
`from mcp_coder.utils.log_utils import token_fingerprint`,
the `._config_diagnostics` names the moved code uses, and
`from ._exceptions import LLMAuthError, LLMConnectionError`.
Keep the two lazy `from . import _models` imports as they are (step 7 confirms
they resolve to the submodule). Product texts stay literal here; step 6 replaces them.

`verification.py` keeps: `_check_mcp_adapter_packages`, `verify_langchain`,
and the whole MCP-server section (`verify_mcp_servers` unchanged).

```python
_PROBE_KEYS = ("ollama_daemon", "ollama_tools_capability", "available_models", "model_check")

def verify_langchain(check_models: bool = False, mcp_config_path: str | None = None) -> dict[str, Any]: ...
```

## HOW

1. **Tests first.**
   - Search tests and production code **by name** (targets are f-strings:
     `_LC_VERIFY`, `_VERIFICATION`, `_lc_verify`) for every moved name and for the
     `_config_diagnostics` names the moved code imports (`resolve_target`,
     `describe_effective_config`, `validate`, `mode_of`, `redirect_env_in_effect`,
     `_targets_match`, `NON_URL_TARGETS`, `_API_KEY_ENV`, `_KEYLESS_ENV`) plus
     `token_fingerprint` and `suggest`. Every patch or import of one of them on
     `verification` moves to `mcp_coder.llm.providers.langchain._provider_checks`.
     Add a `_PROVIDER_CHECKS = "mcp_coder.llm.providers.langchain._provider_checks"`
     constant next to the existing ones where convenient.
   - `test_langchain_verification.py`: the five four-value `side_effect` sequences
     for `_check_package_installed` (core, backend, mcp_adapters, langgraph) and the
     four two-value sequences used with `_check_mcp_adapter_packages` keep their
     values; only the single patch target changes to `_provider_checks`. The call
     order holds because the MCP check runs after `check_provider`.
   - Patches that stay on `verification`: `_load_langchain_config`,
     `_check_mcp_adapter_packages`, `verify_mcp_servers` and the MCP-server helpers.
   - New `test_langchain_provider_checks.py` (keeps `test_langchain_verification.py`
     under the size limit):
     - `check_provider` takes the config as an argument (no `_load_langchain_config` patch needed) and returns no `mcp_adapters` / `langgraph` keys;
     - its `overall_ok` is True for a configured backend with packages installed even when the MCP packages are missing (patch `_provider_checks._check_package_installed` with a side effect `lambda p: p not in ("langchain_mcp_adapters", "langgraph")`);
     - `verify_langchain` with the same patch returns `overall_ok` False and both MCP rows not ok;
     - `_check_mcp_adapter_packages` uses the `_provider_checks` attribute: one patch on `_provider_checks._check_package_installed` is seen by it.
2. Create `_provider_checks.py`; move the helpers; build `check_provider` from the
   body of today's `verify_langchain` **minus** the config load and the MCP block,
   in the same statement order.
3. `verification.py`:
   - `from . import _provider_checks` and keep `from ._config_source import _load_langchain_config`;
   - `_check_mcp_adapter_packages` calls `_provider_checks._check_package_installed(...)` (attribute lookup, never `from … import`);
   - rewrite `verify_langchain` as in ALGORITHM; keep its docstring's return description;
   - delete imports only the moved code used (`importlib.util`, `os`, `urlparse`, `suggest`, `token_fingerprint`, the `_config_diagnostics` and `_exceptions` imports) and the unused `logging` / `logger`. Keep `asyncio`, `re`, `shutil`, `Any`, `_load_mcp_server_config`.
4. `verify_sections._print_langchain_readiness_warning`: import `_BACKEND_PACKAGES`
   and `_check_package_installed` from `...llm.providers.langchain._provider_checks`.
5. Final search: no moved name is still imported or patched via `verification`
   anywhere in `src/` or `tests/`.

## ALGORITHM

`check_provider` keeps today's `overall_ok` without the MCP terms:
```
ok = bool(backend and result["backend_package"]["ok"])
if backend == "ollama": ok = ok and daemon ok [and tools-capability ok if present]
ok = ok and all(f["ok"] is not False for f in findings.values())
result["overall_ok"] = ok
```

`verify_langchain`:
```
rows = _provider_checks.check_provider(_load_langchain_config(), check_models=check_models)
provider_ok = rows.pop("overall_ok")
mcp = _check_mcp_adapter_packages()
result = {}
for key, row in rows.items():
    if key in _PROBE_KEYS and "mcp_adapters" not in result: result.update(mcp)
    result[key] = row
if "mcp_adapters" not in result: result.update(mcp)
mcp_ok = mcp["mcp_adapters"]["ok"] and mcp["langgraph"]["ok"]
result["overall_ok"] = provider_ok if mcp_ok else False
```
`provider_ok if mcp_ok else False` reproduces today's
`bool(backend and pkg and mcp and lg) and …` exactly, including non-bool probe
`ok` values (a plain `and` would return `provider_ok` where today returns `False`).
`langchain_core` stays out of `overall_ok`, as today.

## DATA

`check_provider` → `dict[str, Any]`: rows `backend, model, api_key, <finding rows>,
effective_config (list), langchain_core, backend_package, [base_url_shape],
[base_url_redirect], [api_key_override], [ollama_daemon], [ollama_tools_capability],
[available_models], [model_check], overall_ok`.
`verify_langchain` → same plus `mcp_adapters`, `langgraph` at today's position.
