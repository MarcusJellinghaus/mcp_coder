# Decisions

1. **Guard `max()` against empty iterator in Step 3** — Use `default=0` in the `max_name` computation so that when all servers failed (no tool names exist), `max()` does not raise `ValueError`.

2. **Set `.description = None` on `_make_tools_response(count)` mocks in Step 2** — The existing helper must explicitly set `.description = None` on each mock tool object. Without this, `MagicMock` auto-attributes make `t.description or ""` produce a truthy `MagicMock` instead of `""`, breaking tuple construction.

3. **Add `test_list_mcp_tools_all_servers_failed` in Step 3** — Cover the edge case where every server failed, ensuring no crash and no tool lines are rendered.
