# Step 1 — Render `api_base_url` row and `token_fingerprint` suffix in GITHUB section

> **Reads first**: `pr_info/steps/summary.md` for context, design rationale, and out-of-scope items.

## Scope

Single TDD commit consuming `mcp-workspace` #176 additions:

- **Tests first** (red): three new tests / tuple updates.
- **Code** (green): four production lines in `src/mcp_coder/cli/commands/verify.py`.
- **Verify**: pylint + pytest + mypy all green.

## WHERE — File paths

| File | Purpose |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | Production change (`_LABEL_MAP` entry + `token_configured` suffix block). |
| `tests/cli/commands/test_verify_format_section_basic.py` | Unit tests for `_format_section` rendering. |
| `tests/cli/commands/test_verify_orchestration.py` | One orchestration test exercising end-to-end wiring. |

## WHAT — Production change (verify.py)

### A. `_LABEL_MAP` (existing dict near `verify.py:218-249`)

Add **one entry** in the GitHub section block (alongside `token_configured`, `authenticated_user`, etc.):

```python
"api_base_url": "API base URL",
```

No specific position required within the dict — `_LABEL_MAP` is a lookup table; insertion order does not affect rendering.

### B. `token_configured` suffix block (existing block at `verify.py:326-331`)

**Current code:**
```python
if key == "token_configured" and entry.get("token_source"):
    src = entry["token_source"]
    suffix = (
        "GITHUB_TOKEN env var" if src == "env" else "~/.mcp_coder/config.toml"
    )
    lines.append(f"{' ' * _VALUE_COLUMN_INDENT}from {suffix}")
```

**New code (add 2 lines, modify the existing append target string):**
```python
if key == "token_configured" and entry.get("token_source"):
    src = entry["token_source"]
    suffix = (
        "GITHUB_TOKEN env var" if src == "env" else "~/.mcp_coder/config.toml"
    )
    fingerprint = entry.get("token_fingerprint")
    if fingerprint:
        suffix = f"{suffix} ({fingerprint})"
    lines.append(f"{' ' * _VALUE_COLUMN_INDENT}from {suffix}")
```

**No other code changes.** The new `api_base_url` row needs zero special-case handling — the existing iteration over `result.items()` in `_format_section` picks it up automatically because upstream emits it as the first key, and `_LABEL_MAP.get(key, key)` resolves the label.

## WHAT — Tests

### Test 1: extend existing tuple (one-word edit)

**File**: `tests/cli/commands/test_verify_format_section_basic.py`

In `TestGitHubLabelMappings._GITHUB_KEYS`, add `"api_base_url"` to the existing tuple. The existing `test_all_github_keys_in_label_map` will then assert the new key is mapped.

```python
_GITHUB_KEYS = (
    "api_base_url",          # <-- ADD
    "token_configured",
    "authenticated_user",
    "repo_url",
    "repo_accessible",
    "branch_protection",
    "ci_checks_required",
    "strict_mode",
    "force_push",
    "branch_deletion",
    "auto_delete_branches",
)
```

### Test 2: parametrized `api_base_url` rendering test

**File**: `tests/cli/commands/test_verify_format_section_basic.py`

Add new test class `TestApiBaseUrlRendering` with one parametrized method covering both the success and fallback shapes. Use the same parametrize style as the existing `TestAutoDeleteBranches.test_auto_delete_branches_value_cases` for consistency.

**Signature:**
```python
class TestApiBaseUrlRendering:
    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "entry, marker, value",
        [
            (
                {"ok": True, "value": "https://api.example.ghe.com"},
                "[OK]",
                "https://api.example.ghe.com",
            ),
            (
                {
                    "ok": False,
                    "severity": "warning",
                    "value": "https://api.github.com (fallback - identifier unresolved)",
                    "error": "Could not determine repository URL from git remote",
                },
                "[ERR]",  # symbol comes from ok=False, NOT from severity="warning"
                "https://api.github.com (fallback - identifier unresolved) "
                "(Could not determine repository URL from git remote)",
            ),
        ],
    )
    def test_api_base_url_value_cases(
        self, entry: dict[str, Any], marker: str, value: str
    ) -> None:
        result: dict[str, Any] = {
            "api_base_url": entry,
            "overall_ok": entry["ok"] is True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        expected_line = _format_row("API base URL", marker, value, indent=2)
        assert expected_line in output
```

The fallback case proves the **`severity`-is-ignored** invariant: an entry with `severity="warning"` still renders `[ERR]` because `ok=False`.

### Test 3: parametrized `token_fingerprint` suffix test

**File**: `tests/cli/commands/test_verify_format_section_basic.py`

Add new test class `TestTokenFingerprintSuffix` with one parametrized method covering three cases.

**Signature:**
```python
class TestTokenFingerprintSuffix:
    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "fingerprint, expected_in_suffix",
        [
            ("ghp_...a3f9", "(ghp_...a3f9)"),  # normal token
            ("****", "(****)"),                 # short-token sentinel
            (None, None),                       # field absent → no parens added
        ],
    )
    def test_fingerprint_appended_when_present(
        self, fingerprint: str | None, expected_in_suffix: str | None
    ) -> None:
        entry: dict[str, Any] = {
            "ok": True,
            "value": "configured (scopes: repo)",
            "token_source": "config",
        }
        if fingerprint is not None:
            entry["token_fingerprint"] = fingerprint
        result: dict[str, Any] = {
            "token_configured": entry,
            "overall_ok": True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        # The 'from ...' suffix line must appear (existing behavior)
        assert "from ~/.mcp_coder/config.toml" in output
        if expected_in_suffix is None:
            # No fingerprint → no parens on the suffix line
            assert "from ~/.mcp_coder/config.toml\n" in output + "\n"
            assert "(" not in [
                ln for ln in output.split("\n") if "from ~/.mcp_coder" in ln
            ][0].split("config.toml", 1)[1]
        else:
            assert expected_in_suffix in output
```

(The `expected_in_suffix is None` branch tolerates the existing `from ~/.mcp_coder/config.toml` line continuing to render with no trailing `(...)`. The simpler assertion is fine — the goal is "no parens after `config.toml`".)

### Test 4: orchestration end-to-end

**File**: `tests/cli/commands/test_verify_orchestration.py`

Add one new test method to `TestVerifyOrchestration`. **No new fixture helper** — define the inline GitHub dict directly in the test (used once). Mirror the structure of existing orchestration tests.

**Signature:**
```python
@patch(f"{_VERIFY}.log_to_mlflow", create=True)
@patch(f"{_VERIFY}.prompt_llm")
@patch(f"{_VERIFY}.verify_mlflow")
@patch(f"{_VERIFY}.verify_claude")
@patch(f"{_VERIFY}.resolve_llm_method")
def test_github_section_renders_diagnostics(
    self,
    mock_provider: MagicMock,
    mock_claude: MagicMock,
    mock_mlflow: MagicMock,
    mock_prompt_llm: MagicMock,
    _mock_log_mlflow: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """api_base_url row and token_fingerprint suffix appear in rendered output."""
    mock_provider.return_value = ("claude", "default")
    mock_claude.return_value = _claude_ok()
    mock_mlflow.return_value = _mlflow_not_installed()
    mock_prompt_llm.return_value = _minimal_llm_response()
    github_with_diagnostics: dict[str, Any] = {
        "api_base_url": {"ok": True, "value": "https://api.example.ghe.com"},
        "token_configured": {
            "ok": True,
            "value": "configured (scopes: repo)",
            "token_source": "config",
            "token_fingerprint": "ghp_...a3f9",
        },
        "overall_ok": True,
    }
    with patch(f"{_VERIFY}.verify_github", return_value=github_with_diagnostics):
        execute_verify(_make_args())
    output = capsys.readouterr().out
    assert "API base URL" in output
    assert "https://api.example.ghe.com" in output
    assert "ghp_...a3f9" in output  # substring, not literal format match
```

The `with patch(...)` block overrides the autouse `_mock_github` fixture for this test only.

## HOW — Integration points

- **Imports**: tests already import `_format_section`, `_format_row`, `_VALUE_COLUMN_INDENT` from `mcp_coder.cli.commands.verify`. No new imports needed in the test files except `pytest` (already imported) and `Any` (already imported).
- **Decorators**: orchestration test follows the existing `@patch(f"{_VERIFY}.X")` stacking pattern. No new patches beyond what existing tests use; the per-test `with patch(f"{_VERIFY}.verify_github", ...)` overrides the autouse fixture.
- **No `pyproject.toml` change.** Upstream `mcp-workspace` is pinned via plain git URL — additions on `main` flow through automatically.
- **No new label-style conventions.** New `_LABEL_MAP` entry follows snake_case → Title Case (existing convention).

## ALGORITHM — Pseudocode for the production change

```
for each (key, entry) in result.items():
    [existing path renders the row using _LABEL_MAP and ok-based symbol]
    if key == "token_configured" and entry has token_source:
        suffix = "<source string>"
        if entry has truthy token_fingerprint:
            suffix = suffix + " (" + token_fingerprint + ")"
        emit indented line "from " + suffix
```

Only the inner `if entry has truthy token_fingerprint` branch is new. The `api_base_url` row needs **zero algorithm change** — it is rendered by the existing per-entry loop body using its `_LABEL_MAP` entry.

## DATA — Shapes

### Upstream `verify_github()` result (relevant fragment)

```python
{
    "api_base_url": {                       # NEW first key (upstream #176)
        "ok": bool,
        "severity": "warning" | "error",    # IGNORED by consumer
        "value": str,
        "error": str | None,
    },
    "token_configured": {
        "ok": bool,
        "value": str,
        "token_source": "env" | "config" | None,
        "token_fingerprint": str | None,    # NEW field (upstream #176)
        "error": str | None,
    },
    # ... other existing keys unchanged ...
    "overall_ok": bool,
}
```

### Rendered lines added

```
  API base URL          [OK]   https://api.<tenant>.ghe.com
                                from ~/.mcp_coder/config.toml (ghp_...a3f9)
```

(The first row is new; the second is the existing suffix line with an appended `(<fingerprint>)`.)

## Definition of Done

1. The 4 production lines are in place.
2. Three new tests / tuple updates exist:
   - `_GITHUB_KEYS` tuple includes `"api_base_url"`.
   - `TestApiBaseUrlRendering.test_api_base_url_value_cases` (parametrized, 2 cases).
   - `TestTokenFingerprintSuffix.test_fingerprint_appended_when_present` (parametrized, 3 cases).
   - `TestVerifyOrchestration.test_github_section_renders_diagnostics`.
3. `mcp__tools-py__run_pylint_check` — green.
4. `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])` — green.
5. `mcp__tools-py__run_mypy_check` — green.
6. `./tools/format_all.sh` run before commit; diff is formatting-only.
7. One commit with a descriptive message (e.g., `verify: render API base URL and token fingerprint in GITHUB section (#933)`).

## LLM Prompt for executing this step

```
Read pr_info/steps/summary.md for the overall context, then read
pr_info/steps/step_1.md for this step's full specification.

Implement step 1 in TDD order:

1. Modify tests/cli/commands/test_verify_format_section_basic.py:
   - Add "api_base_url" to TestGitHubLabelMappings._GITHUB_KEYS tuple.
   - Add new class TestApiBaseUrlRendering with the parametrized
     test_api_base_url_value_cases (success + fallback shapes).
   - Add new class TestTokenFingerprintSuffix with the parametrized
     test_fingerprint_appended_when_present (3 cases).

2. Modify tests/cli/commands/test_verify_orchestration.py:
   - Add test_github_section_renders_diagnostics to TestVerifyOrchestration.
     Use an inline GitHub dict (no new fixture helper), and override
     the autouse _mock_github fixture inside the test using
     `with patch(f"{_VERIFY}.verify_github", return_value=...)`.

3. Run pytest with the fast-mode marker exclusions to confirm the new
   tests fail (red phase).

4. Modify src/mcp_coder/cli/commands/verify.py:
   - Add "api_base_url": "API base URL" to _LABEL_MAP (in the GitHub
     section block).
   - In the token_configured suffix block (~lines 326-331), read
     `fingerprint = entry.get("token_fingerprint")` and, when truthy,
     append " (<fingerprint>)" to the existing suffix string before
     the `lines.append(...)` call. Do NOT change the outer
     `if key == "token_configured" and entry.get("token_source"):` gate.

5. Re-run pytest to confirm green.

6. Run pylint and mypy via the MCP tools; fix any issues.

7. Run ./tools/format_all.sh; confirm the diff is formatting-only.

8. Commit with a single message referencing #933.

Constraints (from summary.md — do NOT violate):
- No pyproject.toml change.
- No severity-aware symbol logic — symbol stays from `ok` only.
- Format-string ownership stays upstream — tests assert substrings,
  never the literal "ghp_...a3f9" shape as a format contract.
- No special-casing for short tokens — "****" renders verbatim via
  Python truthiness.
- No new fixture helper for the orchestration test (inline dict only).
- Use MCP tools for ALL file and quality-check operations
  (per CLAUDE.md mandatory rules).
```
