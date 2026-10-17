# Step 4 — Documentation update

Part of mcp_coder#1180. Read `pr_info/steps/summary.md` first for the overall design.

Depends on Step 3 being complete (describes the shipped behavior, not a plan).

## LLM prompt

> Implement Step 4 of mcp_coder#1180 exactly as specified in `pr_info/steps/step_4.md`,
> using the architecture in `pr_info/steps/summary.md`. This step is documentation
> only — no tests to write. Run `mcp__mcp-tools-py__run_pylint_check`,
> `mcp__mcp-tools-py__run_pytest_check`, and `mcp__mcp-tools-py__run_mypy_check`
> to confirm nothing broke, then make exactly one commit for this step.

## WHERE

`docs/repository-setup/github.md` — add a new subsection after the existing
"## GitHub Token Configuration" section (before "## Workflow Labels Setup"), titled
`## Repo Security Configuration Checks`.

## WHAT

Prose documentation, no code. Content to cover:

- `mcp-coder verify` now prints a `GITHUB SECURITY` section after `GITHUB`, reporting
  — not changing — repo security configuration.
- The two local-file rows (`Dependabot config`, `CodeQL workflow`) need no token and
  work from `.github/dependabot.yml` and `.github/workflows/*.yml` directly.
- The four API-backed rows (`Dependabot alerts`, `Dependabot security`,
  `Secret scanning`, `Secret push protection`) need `Administration: Read` on the
  GitHub token (same permission already listed in the existing fine-grained PAT table
  above in this file) — without it, these rows show `[WARN] not accessible` rather than
  a real on/off state.
- `Code scanning alerts` reflects CodeQL-configured/not-configured only — it does not
  query real alert counts (different permission scope; no repo to verify against yet).
- The whole section is report-only and exit-neutral: it never fails the `verify`
  command. Turning features on/off is a separate GitHub web UI action, not something
  `verify` does.

Include one short example block showing the rendered section (reuse the example from
the issue body verbatim, since it is already the validated shape).

## DATA

N/A — markdown prose only.
