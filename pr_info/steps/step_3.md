# Step 3 — Documentation

**Depends on:** step 2 (documents shipped behaviour). Docs only — no source or
test changes.

## WHERE

| File | Action |
|------|--------|
| `docs/cli-reference.md` | `init` section (lines ~92–116) |
| `docs/repository-setup/repo.md` | `## .gitignore Entries` section (lines ~27–37) |

## WHAT / HOW

### `docs/cli-reference.md`

Mention the gitignore step in the `init` description. Two small edits, both in
the `### init` section:

- **Intro line (~94)** — append to the sentence so it reads: `... deploy the
  bundled Claude Code resources (skills, knowledge base, and agents) into the
  project, and add the VSCodeClaude entries to the project's .gitignore.`
- **`**Description:**` paragraph (~104)** — add a sentence stating that init
  appends any missing VSCodeClaude entries to `<project_dir>/.gitignore` so they
  can be committed, that this runs in both modes (`--just-skills` skips only the
  user config), that it is idempotent, and that a write failure is a warning
  which makes the command exit 1 without skipping the other steps.

Leave the `**Options:**` list and the `**Examples:**` block unchanged. Do not
edit the command summary table at the top of the file.

### `docs/repository-setup/repo.md`

The current block is stale — it lists only `.vscodeclaude_status.txt` of the five
VSCodeClaude entries. Replace the section body with all five, and mark which
lines `mcp-coder init` writes automatically and which stay manual.

Keep the fenced block byte-identical to what init actually writes (including the
exact header `# VSCodeClaude session files (auto-generated)`), and put the
auto/manual annotation in prose *outside* the fence, so the block stays
copy-pasteable and matches `GITIGNORE_ENTRY` in `templates.py`.

```markdown
## `.gitignore` Entries

Files that MCP Coder workflows expect to be gitignored:

```gitignore
# MCP configuration files (may contain sensitive paths)
.mcp.*.json

# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.txt
.vscodeclaude_analysis.json
.vscodeclaude_session.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
```

- **`.vscodeclaude_*` — written automatically.** `mcp-coder init` appends any
  missing entries to `<project_dir>/.gitignore`; commit the result. A
  VSCodeClaude session launch re-appends them as a safety net, so an uncommitted
  block shows up as a dirty `.gitignore` in every session folder.
- **`.mcp.*.json` — add manually.** No tool writes this line.
```

## DATA

None — documentation only.

## Checks

Run the three MCP checks anyway to confirm nothing regressed; nothing should
change. Verify the five entries in `repo.md` match `GITIGNORE_ENTRY` in
`src/mcp_coder/workflows/vscodeclaude/templates.py` exactly, in the same order.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Steps 1 and 2
> are already committed.
>
> Implement step 3 only: the two documentation edits described in the step —
> mention the gitignore step in the `init` section of `docs/cli-reference.md`,
> and replace the stale one-entry `.gitignore` block in
> `docs/repository-setup/repo.md` with all five VSCodeClaude entries plus prose
> marking which lines `mcp-coder init` writes and which stay manual.
>
> Before writing, read `GITIGNORE_ENTRY` in
> `src/mcp_coder/workflows/vscodeclaude/templates.py` and copy the entries
> verbatim, in template order. No source or test changes in this step.
>
> Use MCP tools for all file operations. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`, and
> `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
> to confirm nothing regressed. This step is one commit.
