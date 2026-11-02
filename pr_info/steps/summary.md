# Summary — #1374: name and probe the token scope for code-scanning alerts

## Goal

`mcp-coder verify` stops deriving the **Code scanning alerts** row from CodeQL
presence and shows the real token-scope probe result that mcp-workspace's
`verify_github_security` already returns under the key `code_scanning_alerts`.
`docs/repository-setup/github.md` names the permission (`Code scanning alerts: Read`
/ `security_events`) and explains the probe's outputs and `check_branch_status`'s
skip forms.

## Architectural / design changes

- **Derived row → probed row.** `_derive_code_scanning_alerts` (CodeQL presence →
  always `ok=None`) is deleted. The row now comes from the mcp-workspace probe, like
  the other four API-backed GITHUB SECURITY rows. The `codeql_workflow` row is
  unchanged.
- **One mapping helper, pass-through by default.** A new
  `_map_security_row(key, row)` in `verify_sections.py` is applied to all five
  API-backed rows. It copies the probe's `ok` / `value` / `error` and applies four
  rules:
  1. missing key (older mcp-workspace) → `ok=None`, value `"not accessible"`
     (no KeyError);
  2. `ok=None` + value `"not checked"` → value `"not accessible"` (all five rows);
  3. code scanning only: `ok=False` + value `"scope missing or not configured"` (the
     404) → `ok=None`, value unchanged;
  4. `ok=None` with `error` → value becomes `"<value> (<error>)"`.

  Anything else, including values reworded upstream, passes through unchanged.
- **Error display stays inside the section.** Rule 4 puts the error into the value
  *before* rendering, so the shared renderer `_format_section` (`verify_formatting.py`)
  does not change, and `ok=None` rendering in other sections, including
  branch protection, stays the same (pinned by
  `tests/cli/commands/test_verify_format_section_basic.py`).
- **403 vs 404 by value text.** The probe has no status field, so rule 3 matches the
  probe's `value` string. A test that calls the real `verify_github_security`
  (patching only `BaseGitHubManager` in mcp-workspace) fails if upstream rewords it.
- **Report-only / exit-neutral** as before; no exit-code wiring changes.
- **Known 3xx false positive** (a redirect reads as 200, "scope present") is accepted
  and noted in a code comment at the mapping helper. The comment must not spell out
  the mcp-workspace module path (`tools/check_forbidden_calls.py` text-scans `src/`).

## Resulting verify outcomes (code-scanning row)

| Probe result | Verify row |
|---|---|
| 200 | `[OK] scope present` |
| 403 (not rate-limited) | `[ERR] scope missing or Advanced Security not enabled` |
| 404 | `[WARN] scope missing or not configured` |
| rate limit / network / other | `[WARN] not accessible (<error>)` |
| repo not resolvable (no token) | `[WARN] not accessible (repository not accessible)` — all five API rows |
| key missing | `[WARN] not accessible` |

## Files

Modified:
- `src/mcp_coder/cli/commands/verify_sections.py` — delete `_derive_code_scanning_alerts`
  and the now-unused `cast` import; add `_NOT_ACCESSIBLE`, `_map_security_row`; rewire
  `_print_github_security_section`.
- `tests/cli/commands/conftest.py` — add `code_scanning_alerts` to the autouse
  `_mock_verify_github_security` default.
- `tests/cli/commands/test_verify_sections_security.py` — replace
  `TestDeriveCodeScanningAlerts` with a parametrized `TestMapSecurityRow`; add the
  missing-key section test.
- `tests/cli/commands/test_verify_github_security_section.py` — add the key to
  `_security_api_ok`, `_security_api_fail` and the no-token dict; the no-token test
  expects five rows.
- `docs/repository-setup/github.md` — token section, sample output, API-backed rows,
  Code scanning alerts paragraph.
- `docs/repository-setup/quality-and-security-checks.md` — one phrase (optional item).

Created:
- `tests/cli/commands/test_verify_github_security_probe.py` — tests that call the real
  `verify_github_security` (200/403/404/error and repo-unresolvable).

No new packages or modules in `src/`.

## Steps

1. `step_1.md` — row mapping helper + section wiring + mocked tests/fixtures.
2. `step_2.md` — tests that call the real probe (pin upstream value strings and the no-token outcome).
3. `step_3.md` — documentation.
