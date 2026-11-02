# Step 1 — Row mapping helper and section wiring

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> TDD: write/adjust the tests first, then the code. Run pylint, mypy, and the fast
> pytest suite (`-n auto`, unit markers excluded) and fix until all pass. Format with
> `run_format_code`, then make exactly one commit.

## Precondition

The installed mcp-workspace must return `code_scanning_alerts` from
`verify_github_security` (check with
`get_library_source("mcp_workspace.github_operations._security_probes")`). If it does
not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py`
- `tests/cli/commands/test_verify_sections_security.py`
- `tests/cli/commands/conftest.py`
- `tests/cli/commands/test_verify_github_security_section.py`

## WHAT

```python
_NOT_ACCESSIBLE: dict[str, Any] = {
    "ok": None, "value": "not accessible", "severity": "warning",
}

def _map_security_row(key: str, row: Mapping[str, Any] | None) -> dict[str, Any]:
    """Map one probe result to its GITHUB SECURITY row (pass-through + 4 rules)."""
```

`Mapping` from `collections.abc`. If mypy rejects passing a `CheckResult` TypedDict
as `Mapping[str, Any]`, use `Mapping[str, object]`.

Delete `_derive_code_scanning_alerts` and drop `cast` from the `typing` import (no other
users).

## ALGORITHM

```
entry = dict(row) if row is not None else dict(_NOT_ACCESSIBLE)
if entry["ok"] is None and entry["value"] == "not checked": entry["value"] = "not accessible"
if key == "code_scanning_alerts" and entry["ok"] is False
        and entry["value"] == "scope missing or not configured": entry["ok"] = None
if entry["ok"] is None and entry.get("error"): entry["value"] = f"{value} ({error})"
return entry
```

Comment above the helper (wording free, but no `mcp_workspace.` module path in `src/`):
a 3xx from the mcp-workspace probe returns normally and is reported as 200 ("scope
present") — known false positive, accepted.

## HOW

In `_print_github_security_section`, keep the explicit dict and its row order:

```python
api = verify_github_security(project_dir)
{
    "dependabot_config": _check_dependabot_config(project_dir),
    "dependabot_alerts": _map_security_row("dependabot_alerts", api.get("dependabot_alerts")),
    ... same for dependabot_security_updates, secret_scanning, secret_scanning_push_protection ...
    "codeql_workflow": _check_codeql_workflow(project_dir),
    "code_scanning_alerts": _map_security_row("code_scanning_alerts", api.get("code_scanning_alerts")),
}
```

Update the docstring (no more `_derive_code_scanning_alerts` reference). `_format_section`
is **not** changed: it ignores `error` on `ok=None` rows other than `branch_protection`,
so the error is not printed twice.

## DATA

`_map_security_row` returns a plain dict with keys `ok` (`True|False|None`), `value`
(str), `severity`, and optionally `error` (left in place; on `ok=False` rows the
renderer still appends it as before).

## Tests (write first)

`tests/cli/commands/test_verify_sections_security.py`:
- Remove `_derive_code_scanning_alerts` import and `TestDeriveCodeScanningAlerts`;
  update the module docstring (it now also covers the row mapping).
- Add `TestMapSecurityRow` with one `@pytest.mark.parametrize` table
  `(key, row, expected_ok, expected_value)`:
  - code scanning 200: `ok=True, "scope present"` → `True, "scope present"`
  - code scanning 403: `ok=False, "scope missing or Advanced Security not enabled"` → unchanged
  - code scanning 404: `ok=False, "scope missing or not configured"` → `None`, value unchanged
  - `secret_scanning` with `ok=False, "scope missing or not configured"` → stays `False` (demotion is code scanning only)
  - code scanning error: `ok=None, "not accessible", error="network error: boom"` → `None, "not accessible (network error: boom)"`
  - `dependabot_alerts` repo-unresolvable: `ok=None, "not checked", error="repository not accessible"` → `None, "not accessible (repository not accessible)"`
  - code scanning missing key: `None` → `None, "not accessible"`
  - code scanning unrecognised: `ok=False, "something reworded"` → unchanged
- Add one section test for the missing key: request the autouse
  `_mock_verify_github_security` fixture, set its `return_value` to the conftest
  default minus `code_scanning_alerts`, call
  `_print_github_security_section(tmp_path, STATUS_SYMBOLS)`, and assert via `capsys`
  that the `Code scanning alerts` line contains `[WARN]` and `not accessible`
  (no exception). `STATUS_SYMBOLS` is in `verify_formatting`.

`tests/cli/commands/conftest.py`: add to the autouse default
`"code_scanning_alerts": {"ok": True, "value": "scope present", "severity": "warning"}`.

`tests/cli/commands/test_verify_github_security_section.py`:
- `_security_api_ok` / `_security_api_fail`: add `"code_scanning_alerts": dict(row)`.
- `test_no_token_rows_render_as_warn`: add `code_scanning_alerts` to the inline dict,
  assert `len(no_token_rows) == 5`, and name all five rows in the docstring
  (Dependabot alerts, Dependabot security, Secret scanning, Secret push protection,
  Code scanning alerts).
- Exit-neutral test unchanged (still covers report-only behaviour).
