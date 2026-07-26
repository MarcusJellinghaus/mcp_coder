# Step 3 — Presentation: `env_setup` probe stays `connected` on needs-auth-only

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_3.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/icoder/env_setup.py` — `_probe_exposed_mcp_tools` (~lines 100–131)
- Tests: `tests/icoder/test_env_setup.py`

## WHAT

Change the status classification so `needs-auth` connectors do not land in the `pending` bucket. Current code:

```python
if find_fatal_mcp_servers(system_message):
    status = "fatal"
elif find_unavailable_mcp_servers(system_message):
    status = "pending"
else:
    status = "connected"
```

New behavior: split `find_unavailable_mcp_servers` results by status value using `MCP_NEEDS_AUTH_STATUS` (import inside the function next to the existing guard imports). Only genuinely pending servers produce `pending`; needs-auth connectors are listed at info level and do not affect the status.

## ALGORITHM

```
fatal = find_fatal_mcp_servers(system_message)            # step 1 already excludes needs-auth
unavailable = find_unavailable_mcp_servers(system_message)
needs_auth = {k: v for k, v in unavailable.items() if v == MCP_NEEDS_AUTH_STATUS}
pending = {k for k in unavailable if k not in fatal and k not in needs_auth}
status = "fatal" if fatal else ("pending" if pending else "connected")
if needs_auth: logger.info("Unauthenticated account connector(s), not part of MCP health assessment: %s", sorted(needs_auth))
```

## DATA

- Return type of `_probe_exposed_mcp_tools` unchanged: `tuple[str | None, int | None]`; status values remain `"fatal" | "pending" | "connected"` — no new bucket.

## TESTS (write first)

Follow the existing mocking pattern in `tests/icoder/test_env_setup.py` (mock `prompt_llm`, feed a `raw_response["system"]` init event):
- Only non-connected servers are `needs-auth` → status `"connected"`.
- `needs-auth` + one `pending` server → status `"pending"`.
- `needs-auth` + one `failed` server → status `"fatal"`.
- Info log lists the connectors (use `caplog`).

## Commit

`fix: env_setup MCP probe treats needs-auth connectors as healthy, info-only (#1090)`
