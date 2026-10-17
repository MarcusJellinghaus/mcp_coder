# Step 2 — Local check: CodeQL workflow + derived Code scanning alerts row

Part of mcp_coder#1180. Read `pr_info/steps/summary.md` first for the overall design.

No dependency on mcp-workspace#314 — proceeds unconditionally.

## LLM prompt

> Implement Step 2 of mcp_coder#1180 exactly as specified in `pr_info/steps/step_2.md`,
> using the architecture in `pr_info/steps/summary.md`. Write the tests first, then the
> implementation, until they pass. Run `mcp__mcp-tools-py__run_pylint_check`,
> `mcp__mcp-tools-py__run_pytest_check`, and `mcp__mcp-tools-py__run_mypy_check`; all
> must pass. Then make exactly one commit for this step.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py` — add both functions (appended after
  `_check_dependabot_config` from Step 1).
- `tests/cli/commands/test_verify_sections_security.py` — append test classes
  `TestCheckCodeqlWorkflow` and `TestDeriveCodeScanningAlerts` to the file created in
  Step 1.

## WHAT

```python
def _check_codeql_workflow(project_dir: Path) -> CheckResult:
    """Scan .github/workflows/*.yml|*.yaml for a step using github/codeql-action."""

def _derive_code_scanning_alerts(codeql_result: CheckResult) -> CheckResult:
    """Derive the Code scanning alerts row from CodeQL presence only (no real counts)."""
```

## HOW

- `re` is already imported in `verify_sections.py` (used by `_KEY_REGEX`) — reuse it,
  add one new module-level compiled pattern.
- Detection is **content-based**, not filename-based: per the issue, a filename glob
  (`*codeql*.yml`) is wrong in both directions. Scan raw file text for a line matching
  a `uses:` step whose value starts with `github/codeql-action`, regardless of which
  file it's in.
- `_derive_code_scanning_alerts` reads only `codeql_result["ok"]`; it never calls any
  GitHub API (out of scope per the issue — no `code-scanning/alerts` query).
- Both rows: `severity="warning"` always. `_check_codeql_workflow` is deterministic
  (`ok=True`/`False`, same reasoning as Step 1). `_derive_code_scanning_alerts` always
  returns `ok=None` — it reflects "configured but alert counts not checked" or "not
  configured", never a verified positive/negative.

## ALGORITHM

`_check_codeql_workflow`:
```
pattern = regex matching: optional leading "- ", then "uses:", optional quote, "github/codeql-action"
workflows_dir = project_dir / ".github" / "workflows"
if workflows_dir exists:
    for each *.yml and *.yaml file in it (sorted, for determinism):
        if pattern found in file text: return ok=True, value=f"found in {filename}"
return ok=False, value="no workflow step uses github/codeql-action"
```

`_derive_code_scanning_alerts`:
```
if codeql_result["ok"] is True:
    return ok=None, value="configured (alert counts not checked)"
return ok=None, value="not configured (no CodeQL workflow)"
```

The exact wording `"not configured (no CodeQL workflow)"` must match the issue's own
rendered example verbatim.

## DATA

```python
CheckResult(ok=True, value="found in ci.yml", severity="warning")
CheckResult(ok=False, value="no workflow step uses github/codeql-action", severity="warning")
CheckResult(ok=None, value="not configured (no CodeQL workflow)", severity="warning")
```

## Tests (write first)

`TestCheckCodeqlWorkflow` (using `tmp_path`):

- `test_no_workflows_dir_returns_false`.
- `test_workflow_with_unrelated_content_returns_false` — a `.github/workflows/ci.yml`
  with no CodeQL step.
- `test_codeql_step_in_non_obvious_filename` — place the CodeQL `uses:` step inside a
  file named e.g. `build.yml` (not `*codeql*`) → `ok=True`, confirming detection is not
  filename-based.
- `test_quoted_uses_value` — `uses: "github/codeql-action/analyze@v3"` (quoted) still
  matches.

`TestDeriveCodeScanningAlerts`:

- `test_codeql_present_yields_configured` — feed an `ok=True` `CheckResult` → value
  contains `"configured"`.
- `test_codeql_absent_yields_not_configured` — feed an `ok=False` `CheckResult` → value
  equals exactly `"not configured (no CodeQL workflow)"`.
- Both cases assert `ok is None` on the returned result.
