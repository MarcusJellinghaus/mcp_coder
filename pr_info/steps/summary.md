# Summary — Extend `mcp-coder verify` with repo security configuration checks

Issue: mcp_coder#1180 (part of epic #1163). Builds on #1179 (merged) — reuses its
tri-state `CheckResult` convention (`ok: True | False | None`).

## Problem

`mcp-coder verify` checks GitHub *token/API access* (`GITHUB` section) but nothing
checks repo-level *security configuration*: dependabot, CodeQL, secret scanning. A repo
can pass `verify` cleanly with all of that off.

## Blocking dependency

The four API-backed rows (secret scanning, secret scanning push protection, dependabot
security updates, dependabot alerts) need a new read-only primitive,
`verify_github_security(project_dir) -> dict[str, CheckResult]`, from companion issue
**mcp-workspace#314**. As of this plan, that primitive is **not yet present** in the
installed `mcp-workspace` package. `mcp-workspace` is an unpinned git dependency, so it
propagates automatically on the next reinstall once #314 merges — no version bump
needed here.

Steps 1 and 2 have no dependency on #314 and can proceed now. Step 3 (wiring in the
API-backed rows) checks the precondition first; see step_3.md. Step 4 depends on Step 3
being complete — it documents the shipped `GITHUB SECURITY` section, including the
API-backed rows — so it is transitively blocked on #314 whenever Step 3 blocks.

## Architectural / design changes

- **New section, existing formatters.** A `GITHUB SECURITY` section is added to
  `execute_verify`'s output, printed right after the existing `GITHUB` section, via the
  same `_format_section` / `_format_row` helpers every other section uses in
  `verify_formatting.py`. No new status marker: `ok=None` continues to mean "cannot
  verify" (API rows under permission constraints), exactly like every other section.
- **Two data sources, two different determinism levels.**
  - *Local-file checks* (`.github/dependabot.yml`, `.github/workflows/*.yml`) live
    entirely in `mcp_coder`, need no token, and are fully deterministic: a file is
    either present-and-valid or it isn't, so these two rows only ever report
    `ok=True`/`False` — never `None`. This mirrors the existing
    `_print_project_section` pattern of reading `pyproject.toml` directly from
    `project_dir`.
  - *API-backed checks* (secret scanning, push protection, dependabot security
    updates, dependabot alerts) come from the new mcp-workspace primitive and can
    genuinely be unverifiable (token lacks `Administration: Read`), so they use the
    full `True | False | None` range.
- **Layering preserved.** Verdict classification for the API rows stays inside
  mcp-workspace (`verify_github_security`), matching `_permission_probes.py` — not
  split into "raw data here / policy there." `mcp_coder` only merges, labels, and
  prints; it gains no PyGithub dependency.
- **`verify_sections.py` owns row assembly**, per the issue's Decisions table ("Row
  assembly / ordering"). A new `_print_github_security_section(project_dir, symbols)`
  function there builds one ordered `dict[str, CheckResult]` — local rows interleaved
  with the primitive's four rows, in the row order fixed by the issue — and makes the
  *single* `_format_section("GITHUB SECURITY", ...)` call itself, mirroring the
  existing `_print_project_section` / `_print_environment_section` shape. `verify.py`
  gets one call site (`_print_github_security_section(project_dir, symbols)` right
  after the `GITHUB` section), not inline merge logic.
- **Exit-code wiring: none.** `verify_exit_code._compute_exit_code` is not touched at
  all — no new parameter. The new section's result is simply never passed to it (it
  isn't even built in `verify.py`), which is sufficient to keep it exit-neutral
  (report-only, matching the current Jenkins-unset precedent).
- **`code_scanning_alerts` is derived, not probed.** It reflects the CodeQL row's
  `ok` value only; it does not call the GitHub code-scanning-alerts endpoint (needs a
  different permission scope, no repo to verify against yet — explicitly out of scope).

## Row order (fixed by the issue)

```
dependabot_config
dependabot_alerts
dependabot_security_updates
secret_scanning
secret_scanning_push_protection
codeql_workflow
code_scanning_alerts
```

## Files created or modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify_sections.py` | **modify** — add `_check_dependabot_config`, `_check_codeql_workflow`, `_derive_code_scanning_alerts`, and `_print_github_security_section` (merges local + API-backed rows, prints the section) |
| `src/mcp_coder/cli/commands/verify_formatting.py` | **modify** — add 7 `_LABEL_MAP` entries for the new row keys |
| `src/mcp_coder/cli/commands/verify.py` | **modify** — one call: `_print_github_security_section(project_dir, symbols)` right after the `GITHUB` section |
| `src/mcp_coder/mcp_workspace_github.py` | **modify** — re-export `verify_github_security` |
| `docs/repository-setup/github.md` | **modify** — document the new section and its rows |
| `tests/cli/commands/test_verify_sections_security.py` | **new** — unit tests for the two local-file checks + the derivation function |
| `tests/cli/commands/test_verify_github_security_section.py` | **new** — orchestration test: section renders, exit code unaffected |
| `tests/cli/commands/conftest.py` | **modify** — add an autouse fixture mocking `verify_github_security` (keeps unrelated orchestration tests hermetic) |

## Steps

1. `step_1.md` — Local check: `_check_dependabot_config` (TDD, no dependency on #314)
2. `step_2.md` — Local check: `_check_codeql_workflow` + `_derive_code_scanning_alerts` (TDD, no dependency on #314)
3. `step_3.md` — Wire in `verify_github_security` + render `GITHUB SECURITY` section (**blocked on mcp-workspace#314**)
4. `step_4.md` — Documentation update (**depends on Step 3 completing — transitively blocked whenever Step 3 is**)

Each step is one commit: tests, implementation, and `run_pylint_check` / `run_pytest_check` / `run_mypy_check` all passing before moving to the next step.
