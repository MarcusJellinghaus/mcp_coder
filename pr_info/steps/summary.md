# Summary: Fine-grained PAT permissions in `github.md` include writes (#1394)

## Problem

`docs/repository-setup/github.md` → *GitHub Token Configuration* lists only read
permissions for a fine-grained PAT. A token built from that list passes
`mcp-coder verify` and then fails on the first workflow write (branch creation,
label change, comment, PR creation, merge).

## Design change (documentation architecture)

- **Single source of truth:** `github.md` *GitHub Token Configuration* becomes the
  only place that lists token permissions.
  - Fine-grained: a table of what the token needs today, with read and write levels,
    plus the unconfirmed mappings.
  - Classic: a conditional `workflow` scope bullet.
  - A **Check runs limitation** block and a **Required in the future** block.
- **Links, not copies:** `label-setup.md` and `config.md` drop their own scope or
  permission wording and link to
  `../repository-setup/github.md#github-token-configuration`.
- **Jenkins credential:** `config.md` explains that the `github_credentials_id` PAT
  serves both sides:
  - it is the workflows' API token (exported as `GITHUB_TOKEN`, overriding
    `[github] token`);
  - it is the git checkout/push credential.

  So it needs Workflows write when pushes may change `.github/workflows/`.

No code, no tests, no configuration changes. No new headings, so the existing
anchors stay valid.

## Files modified

| File | Change |
|---|---|
| `docs/repository-setup/github.md` | Token section rewritten (table, `verify` note, code-scanning consequences, Classic `workflow` bullet, two bold-lead-in blocks) |
| `docs/getting-started/label-setup.md` | `repo`-scope sentence → link |
| `docs/configuration/config.md` | Auto-merge caveat links the permission; *GitHub Credentials Setup* rewritten around the link |

No files are created, apart from these plan files.

## Steps

1. [step_1.md](step_1.md): all three doc edits in one commit (one logical change:
   source of truth plus the links to it).

## Testing

Docs only, so TDD does not apply. `tests/cli/commands/test_define_labels_actions.py`
reads `github.md` and `label-setup.md` to check that the generated workflow snippets
are still there. Run it to confirm the edits did not disturb those snippets.
