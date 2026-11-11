# Step 7 — New `=== LLM TEST` section

## LLM prompt

> Read `pr_info/steps/summary.md` (section 5) and this file. Implement step 7
> only: give the smoke test, test prompt, tools-exposed rows and the `--debug`
> line their own `=== LLM TEST` section, document it, and add the streaming
> test. Tests first, then code. Run pylint, pytest (fast unit filter,
> `-n auto`), mypy; all must pass. One commit.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` (`_run_verify`)
- `docs/cli-reference.md` (the `### verify` section list)
- new `tests/cli/commands/test_verify_llm_test_section.py`
- `tests/cli/commands/test_verify_sections_orchestration.py`
  (`test_malformed_config_short_circuits_downstream`)

## WHAT / ALGORITHM

In `_run_verify`, immediately before the `# 3b. MCP edit smoke test` block:

```
if mcp_config_ok is not False:
    out.open("LLM TEST")        # header shows while the smoke test / prompt run
... 3b smoke test (unchanged condition) ...
... 3c test prompt (unchanged condition) ...
out.close()                      # before verify_mlflow; no-op when not opened
```

The smoke test's condition (`mcp_config_resolved and mcp_config_ok is not False`)
implies the prompt's (`mcp_config_ok is not False`), so one `open` covers both:
the section opens before the smoke test, or before the test prompt when there
is no `.mcp.json`. A malformed `.mcp.json` (`mcp_config_ok is False`) opens
nothing — same as today's output for that path.

`docs/cli-reference.md`: in the sentence listing the report sections, replace
"the MCP servers (smoke test) and MLflow" with
"the MCP servers, `LLM TEST` (MCP edit smoke test and a test prompt) and MLflow".

## Tests (write first)

`tests/cli/commands/test_verify_llm_test_section.py`:

- `test_llm_test_section_holds_smoke_and_prompt_rows`: under
  `_make_verify_mocks()`, output has `=== LLM TEST`, and the
  `MCP edit smoke test`, `Test prompt` and `Tools exposed to model` lines all
  sit between `=== LLM TEST` and `=== MLFLOW`.
- `test_llm_test_section_without_mcp_json`: `resolve_mcp_config_path` → `None`;
  `=== LLM TEST` present, `Test prompt` follows it, no smoke-test row.
- `test_debug_line_inside_llm_test`: `prompt_llm` raises `RuntimeError("x")`;
  the `Test prompt … FAILED` row and `Run with --debug for detailed diagnostics.`
  are inside LLM TEST.
- `test_sections_stream_before_test_prompt` (its own test; no full-output
  assertions because reading `capsys` drains it):
  ```python
  seen: list[str] = []
  def _prompt(*_a, **_k):
      seen.append(capsys.readouterr().out)
      return _minimal_llm_response()
  mocks["prompt_llm"].side_effect = _prompt
  ```
  Assert in `seen[0]`: `=== CONFIG`, `=== GITHUB`, `=== LLM PROVIDER` and
  `=== MCP CONFIG` headers with their rows already printed (e.g. the
  `.mcp.json` row), and the `=== LLM TEST` header printed; `=== MLFLOW` not yet.

`test_verify_sections_orchestration.py`
`test_malformed_config_short_circuits_downstream`: add
`assert "=== LLM TEST" not in output`.

## DATA

No data-structure changes.
