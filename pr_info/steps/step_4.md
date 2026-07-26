# Step 4 — Presentation: `verify_formatting` row stays OK on needs-auth-only

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_4.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/cli/commands/verify_formatting.py` — `_format_tools_exposed_section` (~lines 342–417)
- Tests: `tests/cli/commands/test_verify_format_mcp_section.py`

## WHAT

Exclude `needs-auth` servers from the `pending` bucket so the "MCP tools exposed to model" row stays a success when the only non-connected servers are unauthenticated account connectors. List those connectors on an extra info line, clearly labeled as outside the health assessment.

Current pending computation:
```python
pending = {k: v for k, v in unavailable.items() if k not in fatal}
```
New:
```python
needs_auth = {k: v for k, v in unavailable.items() if v == MCP_NEEDS_AUTH_STATUS}
pending = {k: v for k, v in unavailable.items() if k not in fatal and k not in needs_auth}
```

After the existing `lines`/`hint` assembly, when `needs_auth` is non-empty append an indented note line (same `_VALUE_COLUMN_INDENT` style as the existing hint lines), e.g.:
`-> unauthenticated account connector(s), not part of health assessment: <sorted names>`

## HOW

- Import `MCP_NEEDS_AUTH_STATUS` from `mcp_coder.llm.providers.claude.claude_mcp_guard` alongside the existing guard imports at the top of the file (lines 15–16).
- `ok` semantics unchanged: `True`/`None`/`False` exactly as documented in the docstring; needs-auth-only ⇒ same outcome as all-connected (subject to the existing 0-tools check). Update the docstring accordingly.

## DATA

- Return type unchanged: `tuple[list[str], bool | None]`. The needs-auth note only adds a line to `lines`.

## TESTS (write first)

Follow the existing test pattern for `_format_tools_exposed_section`:
- Init event where the only non-connected servers are `needs-auth` and ≥1 tool exposed → `ok is True`, success marker, output contains the labeled connector note.
- `needs-auth` + `pending` server → `ok is None` (warning), pending list does NOT contain the needs-auth names.
- `needs-auth` + `failed` server → `ok is False`.

## Commit

`fix: verify-formatting MCP row stays OK when only needs-auth connectors are non-connected (#1090)`
