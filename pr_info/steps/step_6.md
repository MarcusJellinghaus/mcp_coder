# Step 6 — `verify.py` inline sections write through the builder

## LLM prompt

> Read `pr_info/steps/summary.md` (sections 1, 4, 5, 7) and this file.
> Implement step 6 only: every remaining `print` in
> `src/mcp_coder/cli/commands/verify.py` goes through `out`;
> `_run_mcp_edit_smoke_test` returns a `Row`; `_format_row` loses its
> `label_width` parameter; no hand-set width remains. Do **not** add the
> LLM TEST header yet (step 7). Tests first, then code. Run pylint, pytest
> (fast unit filter, `-n auto`), mypy, vulture; all must pass. One commit.

## WHERE

- `src/mcp_coder/cli/commands/verify.py`
- `src/mcp_coder/cli/commands/verify_formatting.py` (`_format_row` signature)
- `tests/cli/commands/conftest.py` and the test files listed below

## WHAT

```python
# verify_formatting.py
def _format_row(label: str, marker: str, value: str, *, indent: int) -> str: ...
    # width = _section_label_width([Row(label, marker, value, indent)])

# verify.py
def _run_mcp_edit_smoke_test(project_dir, provider, mcp_config, symbols,
                             env_vars=None, settings_file=None) -> Row: ...
```

## HOW — `_run_verify` section by section

Every section is closed right after its last row; a slow call never runs while
a section is open.

```
_print_environment_section(out)                          # opens + closes itself
config_result = verify_config()
out.open("CONFIG")
  group header  -> out.add("") between groups, out.add(f"  {label}")
  keyed row     -> out.add(Row(first, symbol, rest, 4))
  label-less    -> out.add(Row("", symbol, value, 4)) / Row("", "", value, 4)
  top-level     -> out.add(Row(label, symbol, value))
_print_retired_env_var_warning(symbols, out)              # joins CONFIG
out.close()
... load_prompts / resolve_llm_method (unchanged) ...
prompt_lines: list[Line] = [Row(...), ...]                # was list[str] starting with _pad
out.section("PROMPTS", prompt_lines)
project_ok = _print_project_section(project_dir, symbols, out)
GIT / GITHUB / GITHUB SECURITY / JENKINS / JENKINS JOBS / BASIC VERIFICATION: unchanged from step 4
else-branch: out.add(f"\n  Claude CLI: available at {claude_path} (not active)")   # no section open -> prints now
out.open("LLM PROVIDER"); out.add(Row("Active provider", ...))
env-provider row: out.add(Row(_PROVIDER_ENV_VAR, symbols["warning"], msg))          # no label_width
resolve_mcp_config_path / resolve_claude_settings_path (fast, unchanged)
langchain: out.close(); verify_langchain(...);
           if effective_config: out.section("EFFECTIVE CONFIG", [Row(l, "", v) for l, v in effective_config])
           out.section("LLM PROVIDER DETAILS", ...)
else:      out.add("  (uses Claude CLI — see Basic Verification above)")
           _print_langchain_readiness_warning(symbols, out); out.close()
MCP CONFIG: out.section("MCP CONFIG", [Row(".mcp.json", marker, _msg)])
skipped LangChain MCP (both branches):
           out.section("MCP SERVERS (via langchain-mcp-adapters)",
                       [Row("", symbols["warning"], "server health check skipped (langchain-mcp-adapters not installed)")])
MCP CONFIG WARNINGS: out.section("MCP CONFIG WARNINGS", [Row(l, symbols["warning"], v) for l, v in warnings])
smoke test: out.add(_run_mcp_edit_smoke_test(...))
test prompt: out.add(Row("Test prompt", ...)); out.add(*tools_rows)
failure:     out.add(Row("Test prompt", symbols["failure"], f"FAILED ({category})"))
             out.add("  Run with --debug for detailed diagnostics.")
MLFLOW: unchanged from step 4
INSTALL INSTRUCTIONS: out.section("INSTALL INSTRUCTIONS", [f"  pip install {pip_packages}"])
```

- Remove `_LABEL_WIDTH` and (if unused) `_format_row`, `_pad` from the
  `verify.py` imports; import `Line`, `Row`.
- `_run_mcp_edit_smoke_test`: each `return _format_row(label, m, v, indent=2)`
  → `return Row(label, m, v)`; docstring "Returns: the smoke-test row".
- After this step `verify.py` and `verify_sections.py` contain no `print(`
  call (verify with a search). `_format_row` is still used by `SectionBuilder.add`.

## Tests (write first / update)

- `conftest.py`:
  - add `_SMOKE_ROW = Row("MCP edit smoke test", "[OK]", "edit verified")`;
    `_make_verify_mocks` uses it as `smoke_row`.
  - add autouse fixture
    ```python
    @pytest.fixture(autouse=True)
    def _clear_retired_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
        """Keep CONFIG width independent of the developer's environment."""
        monkeypatch.delenv("MCP_CODER_LLM_LANGCHAIN_ENDPOINT", raising=False)
    ```
    (tests exercising that row already set it explicitly).
- Smoke-test mocks must return a `Row`, never a string or a bare `MagicMock`
  that is actually called:
  - `test_verify_mcp_orchestration.py` (~89, ~126, ~178, ~217, ~251, ~478,
    ~518, ~568, ~636): `return_value=_SMOKE_ROW`; for the bare `@patch(...)` at
    ~217, set `mock_smoke.return_value = _SMOKE_ROW` (or add `return_value=`).
  - `test_verify_orchestration.py` (~395) and
    `test_verify_sections_orchestration.py` (~65): `return_value=_SMOKE_ROW`.
    (~128 is asserted `not_called` — leave it.)
- `test_verify_mcp_edit_smoke.py`: `result` is a `Row`; assert
  `result.marker == "[OK]"` / `"[WARN]"` and `"…" in result.value`.
- `test_verify_format_pad.py`: delete the `_format_row(..., label_width=30)`
  test (keep the `_format_row_prefix(..., label_width=30)` one).
- `test_verify_sections_config.py` `TestProviderEnvVarVisibility`: the
  provider row and `Active provider` row share the value column
  (`_assert_section_aligned` on the LLM PROVIDER chunk), docstring no longer
  mentions an explicit `label_width`.
- `test_verify_mcp_orchestration.py` `TestMcpConfigWarningsDynamicWidth`:
  keep — formula unchanged at indent 2.
- New tests in new file `tests/cli/commands/test_verify_config_width.py`:
  - CONFIG with a `[coordinator.repos.x]` entry
    `"auto_review_implementation true"` widens the whole CONFIG section to value
    column 38 and the `Config file` row aligns with it
    (patch `mcp_coder.cli.commands.verify.verify_config`, run `execute_verify`
    under `_make_verify_mocks`, apply `_assert_section_aligned` to the CONFIG chunk).
  - With `MCP_CODER_LLM_LANGCHAIN_ENDPOINT` set, the retired row joins CONFIG
    and every CONFIG row sits at value column 42.

## DATA

- `_run_mcp_edit_smoke_test` → `Row`.
- `_format_row(label, marker, value, *, indent)` → `str`.
