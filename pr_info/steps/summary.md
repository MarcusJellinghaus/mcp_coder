# Summary — Issue #1275: Base Branch trust gate and ref-name rule (docs)

## Goal

mcp-workspace#342 (merged as mcp-workspace#348) changed how `IssueManager` reads an issue's `### Base Branch` section:

1. **Trust gate:** the section is used only when the issue body is trusted. Untrusted bodies give `base_branch = None`, with no error and no log beyond one log line.
2. **Ref-name rule:** the value must be a valid git ref name. Multi-line or invalid values give `base_branch = None` plus `base_branch_error`. mcp_coder never reads `base_branch_error`.

mcp_coder picks up both without any logic change. This PR updates the docs, four user-facing strings, one docstring and one skill file to match.

## Architectural / design changes

**None to runtime behaviour.** The gate lives in mcp-workspace `IssueManager`, a dependency. No mcp_coder function, signature, data structure or control flow changes.

Design of the documentation change (KISS):

- **One home for the rule.** A new subsection `### Trust and Validation` in `docs/repository-setup/github.md`, with anchor `#trust-and-validation`, holds everything once:
  - the trust rule and its two edge cases;
  - untrusted sections being ignored silently;
  - the ref-name rule;
  - what happens to malformed values;
  - the fallback for each consumer.
- **Everything else points there.** Other docs, the skill file and the user-facing strings carry a short qualifier ("only honoured when the issue body is trusted — see docs/repository-setup/github.md") rather than repeating the rule.
- **The trust rule is linked, not copied.** The full definition stays in the mcp-workspace README (`#commenter-trust`, `#github-configuration`).

## Files modified

| File | Change |
|---|---|
| `docs/repository-setup/github.md` | New `### Trust and Validation` subsection; qualifiers in Parsing Rules, Validation, Epic Branches, Backward Compatibility |
| `docs/cli-reference.md` | Trust qualifier on `rebase --base-branch`, the `rebase` description and `gh-tool get-base-branch` priority 1 |
| `src/mcp_coder/cli/parsers.py` | `--base-branch` help text qualifier |
| `src/mcp_coder/workflows/rebase.py` | `_resolve_base_branch` error message qualifier and docstring |
| `src/mcp_coder/workflows/create_pr/core.py` | "Tip:" log message qualifier |
| `src/mcp_coder/workflows/review/handoff.py` | `_REBASE_HANDOFF["no_base"]` next-step qualifier |
| `tests/workflows/rebase/test_guards.py` | Assert the error mentions trust |
| `.claude/skills/issue_update/SKILL.md` | Ref-name rule and the actual malformed behaviour |

No files are created or deleted, apart from these `pr_info/steps/` plan files.

## Explicitly unchanged

- `.claude/skills/issue_create/SKILL.md` — it states no Base Branch rule.
- Internal docstrings in `cli/commands/gh_tool.py` and `workflow_utils/base_branch.py`.
- `review/handoff.py` `"base_missing"` text ("fix `### Base Branch`").
- `tests/workflows/rebase/test_workflow.py:193-194` — it injects its own copy of the error string through a monkeypatch and does not check the real text.

## Steps

1. `docs/repository-setup/github.md` — the hub section and its pointers.
2. `docs/cli-reference.md` — three trust qualifiers.
3. User-facing strings and the docstring in `src/`, with a test assertion first (TDD).
4. `.claude/skills/issue_update/SKILL.md` — ref-name rule.

## Shared wording

- **Qualifier** (used in step 3): `only honoured when the issue body is trusted — see docs/repository-setup/github.md`. Put it directly after the clause that names `### Base Branch`, not at the end of the string. Brackets and punctuation may adapt to the surrounding string.
- **Link targets:**
  - In-repo: `docs/repository-setup/github.md#trust-and-validation`
  - mcp-workspace: `https://github.com/MarcusJellinghaus/mcp-workspace#commenter-trust` and `https://github.com/MarcusJellinghaus/mcp-workspace#github-configuration`
