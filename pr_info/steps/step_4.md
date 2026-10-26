# Step 4 — `SECURITY.md` and shared-files table row

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`. This is a documentation-only change. Run pylint, pytest (`-n auto`, unit markers), mypy and `run_format_code`; all must pass. Produce one commit.

## WHERE
- `SECURITY.md` (new, repo root)
- `docs/repository-setup/README.md` ("Files Shared With Other Projects" table)

## WHAT

### `SECURITY.md` sections (short, no issue numbers)
1. **Reporting a Vulnerability:** use GitHub private vulnerability reporting only — repository **Security → Report a vulnerability**. Do not open public issues for security problems.
2. **Response:** best effort; no fixed response time.
3. **Supported Versions:** only the latest release on PyPI.
4. **Scope:** bypasses of intended restrictions: permission gates, the issue status workflow (e.g. promoting issues without being trusted), credential handling.
5. **Threat Model:** issue bodies and comments from untrusted users are untrusted LLM input. mcp-coder only acts on issues and feedback from trusted authors (`OWNER`/`MEMBER`/`COLLABORATOR` or allowlisted). Reports that bypass this are in scope. Link: [Trust and Validation](docs/repository-setup/github.md#trust-and-validation).

### README table row
Insert after the `.github/workflows/scorecard.yml` row:
```markdown
| `SECURITY.md` | G | No | No | Adjust contact and scope |
```

## ALGORITHM / DATA
None (documentation only).
