# Step 1 — Part A1: always-on endpoint-shape heuristic in `verify`

See `pr_info/steps/summary.md` for context, the renderer contract, and design
rules. This step adds a pure, no-network string heuristic that flags an
OpenAI `endpoint` that is provably wrong (contains `/completions`), malformed,
or missing the conventional `/v1` suffix. It **must not** affect `overall_ok`.

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py` — new helper + wiring.
- `src/mcp_coder/cli/commands/verify.py` — one `_LABEL_MAP` entry.
- `tests/llm/providers/langchain/test_langchain_verification.py` — unit tests.

## WHAT

New helper in `verification.py`:

```python
def _check_endpoint_shape(
    endpoint: str | None, api_version: str | None
) -> dict[str, Any] | None:
    """Pure string heuristic for a custom OpenAI base URL (no network).

    Returns a verify-style dict, or None when the check does not apply
    (api_version set → Azure path, or no custom endpoint configured).
    """
```

Add `from urllib.parse import urlparse` at module top (stdlib import group).

## HOW (integration)

In `verify_langchain()`, immediately **after** the `backend_package` block and
**before** the MCP-adapter block, add:

```python
if backend == "openai":
    shape = _check_endpoint_shape(config.get("endpoint"), config.get("api_version"))
    if shape is not None:
        result["endpoint_shape"] = shape
```

Do **NOT** reference `result["endpoint_shape"]` in the `overall_ok`
expression — leave that computation untouched.

In `cli/commands/verify.py`, add to `_LABEL_MAP` (LangChain section, near
`"backend_package"`):

```python
"endpoint_shape": "Endpoint",
```

## ALGORITHM (core logic)

```
if api_version or not endpoint:            return None      # Azure gate / nothing to check
if "/completions" in endpoint:             return WARN "...contains '/completions'; use base URL e.g. …/v1 (mcp-coder appends /chat/completions)"
parsed = urlparse(endpoint)
if parsed.scheme not in ("http","https") or not parsed.netloc:
                                           return WARN "...malformed URL; use e.g. https://host/v1"
if not endpoint.rstrip("/").endswith("/v1"):
                                           return INFO "...most relays use …/v1"
return OK endpoint
```

- WARN  → `{"ok": None, "value": "<endpoint> — <guidance>"}`  (renders `[WARN]`, guidance in value)
- INFO  → `{"ok": True, "value": "<endpoint> — most relays use …/v1"}`  (renders `[OK]`)
- OK    → `{"ok": True, "value": endpoint}`

Keep guidance text inside `value` (the renderer only emits a `-> hint` line for
`ok is False`, which this heuristic never uses).

## DATA

Return: `dict[str, Any] | None` with keys `ok` (`None` | `True`) and `value`
(`str`). `None` means "row omitted". The dict is stored under
`result["endpoint_shape"]` and rendered by the existing `_format_section`.

## TESTS (write first)

Add to `test_langchain_verification.py` a class covering `_check_endpoint_shape`:

- `endpoint="https://h/v1/completions"` → `ok is None`, `"/completions"` in value.
- `endpoint="https://h/v1/chat/completions"` → `ok is None` (warning).
- `endpoint="host/v1"` (no scheme) → `ok is None`, "malformed" in value.
- `endpoint="https:///v1"` (no host) → `ok is None`, "malformed" in value.
- `endpoint="https://h/openai"` (valid, no `/v1`) → `ok is True`, "v1" in value (info).
- `endpoint="https://h/v1"` → `ok is True`, value == endpoint (healthy).
- `endpoint="https://h/v1/"` (trailing slash) → `ok is True` (healthy).
- `api_version="2024-02-01"` set → returns `None` (skipped).
- `endpoint=None` → returns `None` (skipped).

Add one `verify_langchain` integration test (mock `_load_langchain_config` to
return `backend="openai"`, a `/completions` endpoint, `api_version=None`):
assert `result["endpoint_shape"]["ok"] is None` **and** `result["overall_ok"]`
is unchanged by the shape finding (i.e. still driven only by packages).

## LLM PROMPT

> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md`
> for the renderer contract and design rules). Work test-first.
>
> 1. Add unit tests to
>    `tests/llm/providers/langchain/test_langchain_verification.py` for a new
>    `_check_endpoint_shape(endpoint, api_version)` helper, covering all cases
>    listed in step_1.md, plus one `verify_langchain` test asserting the
>    `endpoint_shape` row appears for `backend="openai"` and does NOT change
>    `overall_ok`.
> 2. Add `_check_endpoint_shape` to
>    `src/mcp_coder/llm/providers/langchain/verification.py` per the ALGORITHM,
>    using a single `urllib.parse.urlparse` call and no try/except. WARN uses
>    `ok=None` with guidance inside `value`; INFO and healthy use `ok=True`.
> 3. Wire it into `verify_langchain()` after the `backend_package` block, guarded
>    by `backend == "openai"` and `shape is not None`; do NOT add it to the
>    `overall_ok` expression.
> 4. Add `"endpoint_shape": "Endpoint"` to `_LABEL_MAP` in
>    `src/mcp_coder/cli/commands/verify.py`.
>
> Use MCP file tools only. After editing, run `run_pylint_check`,
> `run_pytest_check` (with the fast `-n auto` + `not …integration` exclusions
> from summary.md), and `run_mypy_check`; fix any issues. This is one commit.
