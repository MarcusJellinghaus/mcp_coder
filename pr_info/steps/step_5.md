# Step 5: Documentation updates

**Summary reference:** See `pr_info/steps/summary.md` for overall architecture.

## Goal

Update repository-setup docs to replace hand-copy instructions with `mcp-coder init` and update the compatibility table.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement step 5: update `docs/repository-setup/claude-code.md` to replace hand-copy instructions with `mcp-coder init` references, and update `docs/repository-setup/README.md` compatibility table note. Then run all three code quality checks.

## WHERE

| File | Action |
|------|--------|
| `docs/repository-setup/claude-code.md` | **Edit** — replace hand-copy instructions |
| `docs/repository-setup/README.md` | **Edit** — update compatibility table note |

## WHAT

### `docs/repository-setup/claude-code.md`

In the **`.claude/skills/` - Skills** section, replace the instruction:

> "Copy the skills from mcp-coder or create your own."

With a reference to the automated deployment:

> "Run `mcp-coder init` to deploy skills automatically. To deploy only skills (without config creation), use `mcp-coder init --just-skills`."

Similarly update the **Knowledge Base & Agents** section:

> "Supporting files referenced by skills. Copy as-is to downstream repos:"

Replace with:

> "Supporting files referenced by skills. Deployed automatically by `mcp-coder init`:"

### `docs/repository-setup/README.md`

Update the compatibility table note at the bottom:

> "There is currently no sync/versioning mechanism — when files in this repo change, downstream projects must re-pull manually."

Replace with:

> "Skills, knowledge base, and agents are deployed via `mcp-coder init`. Re-run `mcp-coder init` after upgrading mcp-coder — existing files are never overwritten (delete a file first to refresh it). Other files must be re-pulled manually."

Also update the Quick Setup Checklist to reference `mcp-coder init`:

> "- [ ] Configure Claude Code files (`.claude/`, `.mcp.json`)"

Replace with:

> "- [ ] Deploy Claude skills with `mcp-coder init`"
> "- [ ] Configure Claude Code files (`.claude/CLAUDE.md`, `.mcp.json`)"

## DATA

No code changes — documentation only. No tests needed.
