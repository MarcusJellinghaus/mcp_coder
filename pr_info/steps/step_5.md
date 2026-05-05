# Step 5 — Docs sweep: single `~/.mcp_coder/` path everywhere

## LLM Prompt
> Read `pr_info/steps/summary.md` for context, then implement
> `pr_info/steps/step_5.md`. Mechanical search-and-replace across four
> docs files, plus one prose-level edit in
> `docs/configuration/config.md` and one bullet-list collapse in
> `docs/configuration/mlflow-integration.md`. No source code changes.
> Run all four checks before committing.

## Why this is one commit
A single coherent doc sweep reads as one logical change; splitting per
file would be churn.

## WHERE — 4 files
- `docs/cli-reference.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/configuration/config.md` *(also has a prose edit, see below)*
- `docs/configuration/mlflow-integration.md` *(also has a bullet-list collapse, see below)*

These are the only 4 files in `docs/` that contain `.config/mcp_coder`
patterns (verified by grep). The other 5 files previously listed
(`docs/architecture/architecture.md`, `docs/configuration/claude-code.md`,
`docs/getting-started/label-setup.md`, `docs/repository-setup/github.md`,
`docs/repository-setup/README.md`) are already clean and require no edits.

## WHAT

### Mechanical sweep (all 4 files)
Replace every occurrence of:
- `~/.config/mcp_coder/` → `~/.mcp_coder/`
- `~/.config/mcp_coder` → `~/.mcp_coder`
- `$HOME/.config/mcp_coder` → `~/.mcp_coder` (if present)

Verify `~/.mcp_coder/config.toml` is the only path shown after.

- `docs/configuration/mlflow-integration.md` contains a Windows / Linux
  2-bullet list that collapses from two bullets to a single
  "All platforms: `~/.mcp_coder/config.toml`" line, not just a path swap.

### Prose edit — `docs/configuration/config.md` (lines ~915-930)
Current:
```markdown
### Linux/Containers
- Config path uses `~/.config/mcp_coder/`
- Follows XDG Base Directory Specification
- Ideal for containerized coordinator deployments

### Docker/Containers
Mount config directory as volume:
\```bash
docker run -v ~/.config/mcp_coder:/root/.config/mcp_coder my-container
\```
```

After:
- **Drop** the `### Linux/Containers` subsection entirely (the whole
  block — heading, three bullets — XDG framing no longer applies).
- **Keep** the `### Docker/Containers` subsection but update the
  volume-mount path:
```markdown
### Docker/Containers
Mount config directory as volume:
\```bash
docker run -v ~/.mcp_coder:/root/.mcp_coder my-container
\```
```

(Adjacent `### Windows` subsection stays as-is; the path there is
already correct.)

## HOW
Use `mcp__mcp-workspace__edit_file` per occurrence. For the mechanical
parts, search-and-replace each literal one file at a time. For the
prose section in `config.md`, do the structural delete + targeted edit
as a separate call.

## ALGORITHM
N/A — text edits only.

## DATA
N/A — documentation only.

## Test changes
None.

## Verification
1. `mcp__mcp-tools-py__run_pytest_check` (fast unit tests must still be green)
2. `mcp__mcp-tools-py__run_pylint_check`
3. `mcp__mcp-tools-py__run_mypy_check`
4. `mcp__mcp-tools-py__run_lint_imports_check`
5. Optional: grep for any leftover `\.config[\\/]mcp_coder` occurrences in `docs/` to confirm complete sweep.
6. Commit message: `docs: unify config path to ~/.mcp_coder across all platforms`

## Final acceptance check (after this step lands)
- All issue acceptance bullets satisfied (see `summary.md`).
- `lint-imports` green; `mcp_coder_utils_isolation` contract reflects 4 shims.
- `mcp-coder verify` and `mcp-coder init` print `~/.mcp_coder/config.toml` on Windows (and would on Linux/macOS, though no users there).
