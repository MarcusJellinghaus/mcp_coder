# Step 2 — Add `_validate_mcp_config`, render the validity row, delete `_collect_mcp_warnings`

**Read first:** `pr_info/steps/summary.md`. Depends on Step 1 (the `mcp_config_ok`
parameter already exists on `_compute_exit_code`).

This step delivers the feature end-to-end: parse `.mcp.json` **once**, surface a validity
row **first**, reuse the parse for the existing placeholder-warnings section, and remove the
silent swallow by deleting `_collect_mcp_warnings`.

## WHERE
- Implementation: `src/mcp_coder/cli/commands/verify.py`
  - **Add** `_validate_mcp_config` (place it where `_collect_mcp_warnings` currently sits,
    ~line 124).
  - **Delete** `_collect_mcp_warnings`.
  - **Modify** `execute_verify`: new `MCP CONFIG` block before the `if mcp_config_resolved:`
    health-check block (~line 940); update the `3a-bis` placeholder section (~line 1014) to
    consume the shared variable; pass `mcp_config_ok` into `_compute_exit_code`.
- Tests:
  - `tests/cli/commands/test_verify_orchestration.py` — rewrite class `TestMcpConfigWarnings`
    (its `_collect_mcp_warnings` unit tests) into `_validate_mcp_config` tests; keep the
    rendered-section / dynamic-width tests working against the new wiring.
  - `tests/cli/commands/conftest.py` — re-point the mock (line ~239/258).

## WHAT
New pure helper (parses once, owns all error handling):

```python
def _validate_mcp_config(
    mcp_json_path: str,
) -> tuple[bool | None, str, list[tuple[str, str]]]:
    """Validate .mcp.json and collect ${...} placeholder findings in one parse.

    Returns (ok, message, warnings):
      ok=True  -> well-formed, non-empty mcpServers
      ok=None  -> WARN: parseable but mcpServers is empty ({})
      ok=False -> hard fail: unparseable JSON, or mcpServers missing/not an object
      message  -> human-readable status for the validity row
      warnings -> list of (f"{server} / {env_var}", unresolved_value) pairs
                  (always [] on hard fail)
    """
```

## HOW — integration in `execute_verify`
- Before the existing MCP health-check block, add (default the flag so the `None`-path and
  the placeholder variable are always defined):

```python
    mcp_config_ok: bool | None = None
    mcp_warnings: list[tuple[str, str]] = []
    if mcp_config_resolved:
        _ok, _msg, mcp_warnings = _validate_mcp_config(mcp_config_resolved)
        marker = {
            True: symbols["success"],
            None: symbols["warning"],
            False: symbols["failure"],
        }[_ok]
        print(_pad("MCP CONFIG"))
        print(_format_row(".mcp.json", marker, _msg, indent=2))
        mcp_config_ok = _ok is not False
```
- In the `3a-bis` section, replace `warnings = _collect_mcp_warnings(mcp_config_resolved)`
  with `warnings = mcp_warnings` (keep the rest of that block — the dynamic `label_width`
  and rendering — unchanged).
- In the `_compute_exit_code(...)` call, add `mcp_config_ok=mcp_config_ok`.
- Remove the `_collect_mcp_warnings` function definition and its now-unused imports if any
  become unused (note: `json`, `re`, `Path` are still used by `_validate_mcp_config`).

## ALGORITHM (`_validate_mcp_config`)
```
try: data = json.loads(read_text(path))
except (OSError, JSONDecodeError) as e: return (False, f"invalid JSON ({e})", [])
servers = data.get("mcpServers")
if not isinstance(servers, dict): return (False, "mcpServers missing or not an object", [])
warnings = [(f"{name} / {var}", val)
            for name, srv in servers.items() if isinstance(srv, dict)
            for var, val in srv.get("env", {}).items()
            if isinstance(val, str) and re.search(r"\$\{[^}]+\}", val)]
if not servers: return (None, "config present but no servers defined", warnings)
return (True, "well-formed", warnings)
```

## DATA
- Return: `tuple[bool | None, str, list[tuple[str, str]]]`.
  - `ok`: tri-state hard-fail signal (feeds `mcp_config_ok = ok is not False`).
  - `message`: validity-row value string.
  - `warnings`: same `(label, value)` shape the old `_collect_mcp_warnings` produced, so the
    existing placeholder section and its dynamic-width test are unchanged.

## TDD — write tests first
Rewrite `TestMcpConfigWarnings` unit tests to target `_validate_mcp_config`:
- valid non-empty servers → `(True, "well-formed", [])`.
- empty `{"mcpServers": {}}` → `(None, ...WARN..., [])`.
- unparseable (`"{not json"`) → `ok is False`, `warnings == []` (**silent swallow fixed** —
  this replaces the old `test_invalid_json_returns_empty`).
- `mcpServers` missing / not an object (e.g. `{"mcpServers": []}`) → `ok is False`.
- placeholder present → `ok is True` and `warnings == [("srv / VAR", "${...}")]`
  (preserves the `${...}` behaviour); multiple-servers-multiple-vars case preserved.
- Remove `test_none_path_returns_empty` / `test_missing_file_returns_empty` for the deleted
  function — `None` is guarded at the call site now; a missing file surfaces via `OSError`
  → hard fail.

Orchestration/rendered tests (`execute_verify`):
- `MCP CONFIG` header + `.mcp.json` `[OK]` row printed for a valid config, and the row
  appears **before** the `MCP SERVERS` health-check section (ordering assertion on line
  index).
- Malformed config → `.mcp.json` `[ERR]` row surfaced (not swallowed).
- Empty `{}` → `.mcp.json` `[WARN]` row, exit 0.
- Keep the existing `MCP CONFIG WARNINGS` rendered + dynamic-width tests passing (they now
  flow through `_validate_mcp_config`).

`conftest.py`: change the mock from `_collect_mcp_warnings -> []` to
`_validate_mcp_config -> (True, "well-formed", [])`, and update the yielded dict key.

## Commit
One commit: helper + wiring + deletion + all test updates, all checks green.

## LLM prompt
> Implement Step 2 as described in `pr_info/steps/step_2.md` (context in
> `pr_info/steps/summary.md`; Step 1 already added `mcp_config_ok` to `_compute_exit_code`).
> Use TDD. First update tests: in `tests/cli/commands/test_verify_orchestration.py` rewrite
> `TestMcpConfigWarnings` to test the new `_validate_mcp_config(path) ->
> (ok, message, warnings)` helper (valid, empty `{}` → WARN, unparseable → hard fail with
> `warnings==[]`, `mcpServers` not an object → hard fail, `${...}` placeholder preserved),
> add orchestration tests asserting the `MCP CONFIG` `.mcp.json` row renders and appears
> before the `MCP SERVERS` section (OK/ERR/WARN cases), and keep the existing rendered
> `MCP CONFIG WARNINGS` / dynamic-width tests green; in `tests/cli/commands/conftest.py`
> re-point the `_collect_mcp_warnings` mock to `_validate_mcp_config` returning
> `(True, "well-formed", [])`. Then in `src/mcp_coder/cli/commands/verify.py` add
> `_validate_mcp_config`, add the `MCP CONFIG` validity-row block in `execute_verify`
> before the MCP health-check block, feed its `warnings` into the existing placeholder
> section (replacing the `_collect_mcp_warnings` call), pass `mcp_config_ok=mcp_config_ok`
> into `_compute_exit_code`, and delete `_collect_mcp_warnings`. Use MCP filesystem tools
> only. After editing, run `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> and `mcp__tools-py__run_mypy_check`; fix everything until all pass. Produce exactly one commit.
