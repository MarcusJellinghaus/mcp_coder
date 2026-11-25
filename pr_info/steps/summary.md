# Summary — #1453 docs: one project-config reference, a step-to-request table, and stale statements

## Goal

Documentation only. No `src/` or `tests/` change.

1. A new reference page, `docs/configuration/project-config.md`, lists every
   `[tool.mcp-coder]` key with the file it is read from, its default, its
   readers and what happens on a problem. It also takes over the prompts
   description from `repository-setup/python.md`.
2. `docs/configuration/toolkits.md` gets a `### Step-to-request table` under
   `## Bindings`: which binding each workflow step runs and the Bash grant scope
   of its sessions.
3. Stale statements on main (after #1450, #1451, #1452, #1449, #1454, #1466) are
   fixed. Other pages link to the new page and the new table instead of
   repeating them.

## Design changes (documentation architecture)

- **One home per fact.**
  - Project keys → `project-config.md`.
  - Toolkit config and `verify` toolkit rows → `toolkits.md`.
  - Session grant scopes → `toolkits.md#step-to-request-table`.
  - Setup steps → `setup.md`.
  - `config.md`, `python.md`, `cli-reference.md`, `toolkit-interface.md`,
    `repository-setup/README.md` and the root `README.md` link to those homes
    instead of listing keys or grant scopes.
- **Two configuration systems.** `config.md` presents two systems: the user
  `config.toml`, and the project config (`pyproject.toml` / `mcp-coder.toml`).
  Only the user config reads environment variables.
- **Anchors kept.**
  - `python.md` keeps `#key-sections` and a `### Prompt Configuration` stub
    that holds only a link.
  - `repository-setup/README.md` keeps the heading text
    `Adapting Deployed Files (Non-Python Repos)`; it becomes a `###` under a new
    `## Non-Python Repos`.
  - `toolkits.md` keeps `#configure-a-toolkit`, `#bindings`, `#npm`,
    `#step-fields`, `#defaults`, `#mcp-tools-py`, `#toolmcp-codertoolkit`,
    `#command-toolkit`, `#windows` and `#required-mcp-servers`.
  - `config.md`: the `####` "Environment Variable Overrides" under
    `[llm.langchain]` is renamed "LLM environment variables", so
    `#environment-variable-overrides` (linked from `jenkins.md`) reaches the
    main `##` table.

## Precondition

#1466 (retire `labels-config`) must be on the branch. Step 1 checks this and
writes `pr_info/.blocked.txt` if it is not.

## Files

Created:

- `docs/configuration/project-config.md`

Modified:

- `docs/README.md` (index entry)
- `docs/configuration/config.md`
- `docs/repository-setup/python.md`
- `README.md` (root)
- `docs/cli-reference.md` (prompt, rebase and verify sections)
- `docs/configuration/toolkits.md`
- `docs/architecture/toolkit-interface.md`
- `docs/architecture/architecture.md`
- `docs/repository-setup/README.md`

## Steps

| Step | Content |
|---|---|
| 1 | New `project-config.md` and its index entry. Move the prompts text out of `python.md`. Repoint the prompt links. All `config.md` fixes. Root `README.md` link |
| 2 | Grants, `verify` and formatting: `toolkits.md` (step-to-request table and stale rules, npm example), `toolkit-interface.md`, `cli-reference.md` rebase and verify text, `architecture.md` |
| 3 | `repository-setup/README.md`: `verify` text, `mcp-coder.toml` row, new `## Non-Python Repos` section. Final anchor sweep and full checks |

## Testing approach

There is no new test. The change is documentation only, and the issue asks for
no link checker. The gates are:

- the existing `tests/docs/` tests. `test_cli_reference.py` fails on any `--flag`
  in a `cli-reference.md` command section that the command lacks, so rewritten
  `cli-reference.md` text names no flags;
- a per-step search for every moved or renamed anchor;
- the standard pylint / mypy / pytest checks.
