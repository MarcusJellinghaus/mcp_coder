# Step 4 — Cut down `docs/architecture/dependencies/readme.md`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` exactly.
> Remove what `enforcement.md` now covers, keep the details listed below, fix the two stale
> facts. Keep the file at its path. Make one commit.

## WHERE
`docs/architecture/dependencies/readme.md`

## WHAT — resulting structure

```
# Dependency Management
<one line: why and which tools → ../enforcement.md>
## Why Both import-linter and tach?      (kept, one row fixed)
## Best Practice: Submodule Imports      (kept)
## Refactoring                           (kept)
## When to Add New Rules                 (kept)
## Vulture Whitelist                     (the old Vulture section cut to the whitelist notes)
## Generated Files                       (kept, .dot line fixed)
```

## HOW
- **Replace** the intro line with a pointer to `../enforcement.md`.
- **Delete:** `## Config Files`, `## Tools`, `## Running Checks` (including the
  `lint-imports  # 19 contracts` line and the *For Claude Code* list), `## CI`,
  `## Current Contracts (import-linter)`.
- **Vulture section:** rename to `## Vulture Whitelist`. Drop the *Purpose* and *Command*
  lines, keep the *Whitelist* bullets and the *Note*.
- **Comparison table:** change the row
  `| Submodule boundaries | ✅ `independence` contracts | ❌ (struggles with `__init__.py`) |` to
  `| Submodule boundaries | ✅ `\|` siblings in the layers contract, `forbidden` contracts | ❌ (struggles with `__init__.py`) |`.
  Leave the other rows as they are.
- **Generated Files:** `pydeps_graph.svg` / `.dot` line → `pydeps_graph.dot` (committed) and
  `pydeps_graph.svg` (generate with `tools/pydeps_graph.sh`). Keep the `dependency_graph.html` line.

## ALGORITHM
None.

## DATA
None.

## Checks
- `search_files(pattern="\\d+ contracts|independence. contracts", glob="docs/architecture/dependencies/readme.md")`:
  no counts, no "`independence` contracts".
- The links `../enforcement.md` and `../../processes-prompts/refactoring-guide.md` resolve.

## Commit
`docs(architecture): trim dependencies readme to details not in enforcement.md`
