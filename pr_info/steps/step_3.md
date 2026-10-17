# Step 3 — Wire in API-backed rows + render the GITHUB SECURITY section

Part of mcp_coder#1180. Read `pr_info/steps/summary.md` first for the overall design.

## Precondition (check first, before writing any code)

This step needs `verify_github_security` from the installed `mcp-workspace` package
(companion issue mcp-workspace#314). Check it before doing anything else:

```python
from mcp_workspace.github_operations import verify_github_security  # noqa: F401
```

If this import fails (symbol not present), **write one line to `pr_info/.blocked.txt`**
and stop:

```
Blocked: mcp-workspace#314 (verify_github_security) not yet in installed mcp-workspace package.
```

Do not implement any part of this step on a partial or substitute basis if blocked.

If the import succeeds, read the docstring/signature of `verify_github_security` and
confirm its returned dict's keys match the four assumed below
(`dependabot_alerts`, `dependabot_security_updates`, `secret_scanning`,
`secret_scanning_push_protection`) before hardcoding them in the merge step. If the
keys differ, use the actual keys instead.

## LLM prompt

> Implement Step 3 of mcp_coder#1180 exactly as specified in `pr_info/steps/step_3.md`,
> using the architecture in `pr_info/steps/summary.md`. Check the precondition first.
> If blocked, write the one line to `pr_info/.blocked.txt` and stop — do not proceed
> further in this step. Otherwise, write the tests first, then the implementation,
> until they pass. Run `mcp__mcp-tools-py__run_pylint_check`,
> `mcp__mcp-tools-py__run_pytest_check`, and `mcp__mcp-tools-py__run_mypy_check`; all
> must pass. Then make exactly one commit for this step.

## WHERE

- `src/mcp_coder/mcp_workspace_github.py` — modify (re-export).
- `src/mcp_coder/cli/commands/verify_formatting.py` — modify (`_LABEL_MAP`).
- `src/mcp_coder/cli/commands/verify_sections.py` — modify (new section-printer
  function; merge logic lives here per the issue's "Row assembly / ordering"
  decision).
- `src/mcp_coder/cli/commands/verify.py` — modify (one call site).
- `tests/cli/commands/conftest.py` — modify (new autouse fixture).
- `tests/cli/commands/test_verify_github_security_section.py` — **new file**.

## WHAT

```python
def _print_github_security_section(project_dir: Path, symbols: dict[str, str]) -> None:
    """Merge local-file and API-backed security rows and print the GITHUB SECURITY section."""
```

Per the issue's Decisions table ("Row assembly / ordering"): `verify_sections.py` —
the section-printer module — owns merging the local-file results and the API
primitive's results into one ordered dict and owns the single
`_format_section("GITHUB SECURITY", ...)` call. This matches the existing
`_print_project_section` / `_print_environment_section` shape (a void function in
`verify_sections.py` that builds its section's data and prints it directly);
`verify.py` gets a single call site, not inline merge logic.

## HOW

1. **`mcp_workspace_github.py`**: add `verify_github_security` to the
   `from mcp_workspace.github_operations import (...)` block and to `__all__`.

2. **`verify_formatting.py`**: add to `_LABEL_MAP`:
   ```python
   "dependabot_config": "Dependabot config",
   "dependabot_alerts": "Dependabot alerts",
   "dependabot_security_updates": "Dependabot security",
   "secret_scanning": "Secret scanning",
   "secret_scanning_push_protection": "Secret push protection",
   "codeql_workflow": "CodeQL workflow",
   "code_scanning_alerts": "Code scanning alerts",
   ```
   (All fit within the existing default `_LABEL_WIDTH` of 22 — no `label_width`
   override needed, unlike the "MCP tools exposed to model" row.)

3. **`verify_sections.py`**: add `from typing import Any` (new to this module) and
   `_format_section` to the existing `from .verify_formatting import (...)` block;
   add `from ...mcp_workspace_github import verify_github_security`. Append:
   ```python
   def _print_github_security_section(
       project_dir: Path, symbols: dict[str, str]
   ) -> None:
       """Merge local-file and API-backed security rows, print GITHUB SECURITY.

       Calls `_check_codeql_workflow` once and reuses the result for both the
       `codeql_workflow` row and the `_derive_code_scanning_alerts` input.
       """
       security_api_result = verify_github_security(project_dir)
       codeql_result = _check_codeql_workflow(project_dir)
       github_security_result: dict[str, Any] = {
           "dependabot_config": _check_dependabot_config(project_dir),
           "dependabot_alerts": security_api_result["dependabot_alerts"],
           "dependabot_security_updates": security_api_result[
               "dependabot_security_updates"
           ],
           "secret_scanning": security_api_result["secret_scanning"],
           "secret_scanning_push_protection": security_api_result[
               "secret_scanning_push_protection"
           ],
           "codeql_workflow": codeql_result,
           "code_scanning_alerts": _derive_code_scanning_alerts(codeql_result),
       }
       print(_format_section("GITHUB SECURITY", github_security_result, symbols))
   ```
   `_check_dependabot_config`, `_check_codeql_workflow`, `_derive_code_scanning_alerts`
   are already in this module from Steps 1–2 — no new import needed for those.

4. **`verify.py`**: import `_print_github_security_section` from `.verify_sections`
   (added to the existing import block from that module). Insert directly after the
   existing:
   ```python
   github_result = verify_github(project_dir)
   print(_format_section("GITHUB", github_result, symbols))
   ```
   the single call:
   ```python
   _print_github_security_section(project_dir, symbols)
   ```
   No merge dict is built in `verify.py`, and nothing new is passed to
   `verify_exit_code._compute_exit_code` — its signature and call site stay
   untouched. This is what keeps the section exit-neutral.

5. **`conftest.py`**: add an autouse fixture alongside `_mock_verify_github`. Patch
   target is `verify_sections`, not `verify`, since that is where the merge function
   now calls `verify_github_security`:
   ```python
   @pytest.fixture(autouse=True)
   def _mock_verify_github_security() -> Generator[MagicMock, None, None]:
       """Auto-mock verify_github_security to an all-ok default (keeps CLI tests hermetic)."""
       default = {
           "dependabot_alerts": {"ok": True, "value": "enabled", "severity": "warning"},
           "dependabot_security_updates": {
               "ok": True, "value": "enabled", "severity": "warning",
           },
           "secret_scanning": {"ok": True, "value": "enabled", "severity": "warning"},
           "secret_scanning_push_protection": {
               "ok": True, "value": "enabled", "severity": "warning",
           },
       }
       with patch(
           "mcp_coder.cli.commands.verify_sections.verify_github_security",
           return_value=default,
       ) as mock:
           yield mock
   ```
   This prevents every other orchestration test from making a live GitHub call now
   that `execute_verify` (via `_print_github_security_section`) calls
   `verify_github_security` unconditionally.

## ALGORITHM

Already fully given in HOW step 3 above — it is the complete logic for this step (a
merge, not a computation).

## DATA

The merged dict built inside `_print_github_security_section` is a
`dict[str, CheckResult]` with exactly the 7 keys listed in summary.md's row-order
table, in that order (dict insertion order is what `_format_section` renders).

## Tests (write first)

`tests/cli/commands/test_verify_github_security_section.py`, following the
`_make_verify_mocks` / `_make_args` conventions from `conftest.py`. Patch
`verify_github_security` at `mcp_coder.cli.commands.verify_sections.verify_github_security`
(that is where `_print_github_security_section` calls it, overriding the autouse
conftest fixture per-test as needed):

- `test_section_renders_all_rows` — patch `verify_github_security` to return all
  `ok=True`, run `execute_verify`, assert the captured stdout contains the
  `GITHUB SECURITY` header and all 7 row labels (`Dependabot config`,
  `Dependabot alerts`, `Dependabot security`, `Secret scanning`,
  `Secret push protection`, `CodeQL workflow`, `Code scanning alerts`).
- `test_section_is_exit_neutral_when_all_rows_fail` — patch `verify_github_security`
  to return all `ok=False`, and patch `_check_dependabot_config` /
  `_check_codeql_workflow` (at `mcp_coder.cli.commands.verify_sections`) to also return
  `ok=False`; with every *other* mocked result passing, assert `execute_verify` still
  returns exit code `0`.
- `test_api_result_rows_pass_through_unmodified` — patch `verify_github_security` with
  one row `ok=None` and `value="not accessible (403)"` (simulating a 403 on a
  configured token) and assert that exact row renders as `[WARN]` in the output (via
  `STATUS_SYMBOLS["warning"]`), proving `None` → `[WARN]` with no special-casing added
  in `_print_github_security_section`.
- `test_no_token_rows_render_as_warn` — patch `verify_github_security` with all four
  API-backed rows `ok=None` and `value="no token configured"` — distinct from the
  403 case above, per the issue's acceptance criteria listing "no-token" and
  "API-403" as two separate scenarios — and assert those rows render as `[WARN]` and
  `execute_verify` still returns exit code `0`. (Both scenarios render identically at
  this layer since the three-state classification itself happens in
  `verify_github_security`, not here — this test documents that mcp_coder does not
  need to special-case either path.)
