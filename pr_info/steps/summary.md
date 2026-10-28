# Summary — #1346 Explain why the architecture rules are enforced (`enforcement.md`)

## Goal

Add `docs/architecture/enforcement.md`: a short document on **why** mcp-coder enforces its
architecture mechanically, with one line per tool linking to the tool's docs and its ruleset.
Point the README badge and the related docs at it, and cut what it now covers from the older
docs. Fix the pydeps / tach_docs scripts so they write into `docs/architecture/dependencies/`,
where the committed graph files live.

## Architectural / design changes

No code architecture changes and no config or rule changes. The change is to the documentation
structure:

| Document | Role after this change |
|---|---|
| `docs/repository-setup/quality-and-security-checks.md` (#1181 hub) | **What** runs (unchanged, plus links) |
| `docs/architecture/enforcement.md` (new) | **Why** the architecture rules exist, and the LLM angle; links to tools and rulesets |
| `.importlinter`, `tach.toml`, `pyproject.toml`, `tools/check_forbidden_calls.py`, `vulture_whitelist.py`, `.large-files-allowlist`, `ci.yml` | The rules themselves, with per-rule rationale as comments (unchanged) |
| `docs/architecture/dependencies/readme.md` | Details only: import-linter vs. tach comparison, submodule imports, when to add a rule, vulture whitelist notes, generated files |
| `docs/repository-setup/python.md` *Architecture Enforcement* | Per-tool *Customize* notes plus a link |
| `docs/architecture/architecture.md` §8 | Two-line pointer instead of the enforcement / dead-code subsections |

Design principles:
- **Why, not what.** No document restates individual rules, so a rule change never needs a doc change.
- **No counts.** Link to the ruleset files instead of counting contracts.
- **Facts from the source.** Take facts from `.importlinter`, `tach.toml`, `ci.yml`, `pyproject.toml`
  and `tools/check_forbidden_calls.py`, not from the existing docs.
- **Independence** is not a source-level `independence` contract (the only one,
  `test_module_independence`, covers tests). Sibling independence comes from `|` siblings in
  `layered_architecture`, forbidden contracts such as `jenkins_independence`, and tach `depends_on`.
- **forbidden-calls:** describe the `RULES` that are on `main` (today: the `["git"` argv rule plus the
  `mcp_workspace.git_operations` / `github_operations` import rules; #1350 may move the import rules).

Script fix: `tools/tach_docs.py` and `tools/pydeps_graph.sh` / `.bat` write to
`docs/architecture/dependencies/` (matching the committed files and the `.gitignore` entry).

## Files

### Created
- `docs/architecture/enforcement.md`

### Modified
| File | Step |
|---|---|
| `tests/tools/test_tach_docs.py` | 1 |
| `tools/tach_docs.py` | 1 |
| `tools/tach_docs.sh`, `tools/tach_docs.bat` (header comments) | 1 |
| `tools/pydeps_graph.sh`, `tools/pydeps_graph.bat` | 2 |
| `docs/architecture/dependencies/pydeps_graph.html` (command snippet) | 2 |
| `README.md` (badge) | 3 |
| `docs/README.md` (index entry) | 3 |
| `docs/architecture/dependencies/readme.md` | 4 |
| `docs/repository-setup/python.md` | 5 |
| `docs/architecture/architecture.md` (§8 only) | 6 |
| `docs/repository-setup/quality-and-security-checks.md` | 7 |

### Not modified (links that must stay valid)
- `docs/architecture/dependencies/readme.md` stays at its path (linked from `docs/README.md` and
  `docs/processes-prompts/refactoring-guide.md`).
- `architecture.md` keeps its path and all other headings (`#execution-context-management` is linked
  from `environments.md`).
- `python.md` keeps `## Architecture Enforcement` and `### Dependency Declaration Hygiene`.
- `repo.md#file-size-management` stays as is.
- `.claude/settings.local.json` is out of scope.

## Steps

1. `tach_docs.py` writes to `docs/architecture/dependencies/` (TDD: test first).
2. The pydeps scripts write to `docs/architecture/dependencies/`, plus the viewer snippet.
3. Create `enforcement.md`, update the README badge and the `docs/README.md` entry.
4. Cut down `dependencies/readme.md`.
5. Cut down the `python.md` *Architecture Enforcement* section and fix the MCP note.
6. Replace the `architecture.md` §8 subsections with a pointer.
7. Add `enforcement.md` links to the #1181 hub.
