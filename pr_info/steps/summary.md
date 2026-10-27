# Summary — #1181 Add a quality and security checks overview document

## Goal

One hub page that answers **"which automated checks run on mcp-coder, and why?"** in a few
minutes. Overview plus links only. The details stay in `pyproject.toml`, `ci.yml`,
`.importlinter`, `tach.toml`, `python.md`, `github.md`, `repo.md` and the epic's (#1163) issues.

## Architectural / design changes

None to code or config. **Docs only.**

Documentation architecture:

- New hub page `docs/repository-setup/quality-and-security-checks.md`, mcp-coder only (no
  downstream template, no propagation, not in the shared-files matrix).
- The hub **links out**; it does not copy. The overview table's links column is the full link
  list. Each area section gives the why plus its single most relevant link.
- It becomes the **home of the job-name rule**: required status checks must equal CI job
  names, and matrix entries report under their `name`.
- Inbound links: one README *Detail Documentation* row, plus four identical one-line
  pointers in `python.md` and `github.md`.

## Design decisions (KISS)

- **Current state only.** No roadmaps, no "to be retired". One exception: an inline note that
  `verify` reports CodeQL `[OK]` only because Scorecard's `upload-sarif` step matches the
  `github/codeql-action/*` prefix. Default setup itself is not detected.
- **Keep fast-changing facts out:** no rule-code lists, no ignore lists, no copied CI
  commands or triggers, no source line numbers. Name rule groups by issue number, and CI jobs
  by name (names are what required checks match).
- **Facts come from `ci.yml`, `pyproject.toml` and the live MCP tool list**, not from
  `python.md`/`github.md`/`repo.md`. Those docs hold stale CI facts (#1351). Not fixed here.
- Issue references are plain `#NNNN`.
- No TDD: there is no code. Verification = `check_file_size` + manual link/anchor check.

## Files

| Action | Path |
|---|---|
| Create | `docs/repository-setup/quality-and-security-checks.md` (step 1) |
| Modify | `docs/repository-setup/README.md` — Detail Documentation row (step 2) |
| Modify | `docs/repository-setup/python.md` — pointers under *Architecture Enforcement*, *CI Workflow for Python* (step 2) |
| Modify | `docs/repository-setup/github.md` — pointers under *Repo Security Configuration Checks*, *Code Quality CI* (step 2) |

No folders or modules are created. `pr_info/` must not reach the PR (`check-forbidden-folders`).

## Steps

1. [step_1.md](step_1.md) — write the hub page.
2. [step_2.md](step_2.md) — add the inbound links.
