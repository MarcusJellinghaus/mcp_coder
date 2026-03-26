# Step 2: Update slash commands and docs for `gh-tool set-status`

**References:** [summary.md](summary.md) — Part 3 (continued)

## Goal

Update all references to `mcp-coder set-status` outside source code: slash commands, documentation.

## WHERE

- `.claude/commands/plan_approve.md`
- `.claude/commands/implementation_approve.md`
- `.claude/commands/implementation_needs_rework.md`
- `docs/processes-prompts/development-process.md`
- `docs/cli-reference.md`

## WHAT

### Slash commands (3 files)

Each file has two things to update:
1. **Frontmatter** `allowed-tools:` line: `Bash(mcp-coder set-status *)` → `Bash(mcp-coder gh-tool set-status *)`
2. **Body** command example: `mcp-coder set-status <label>` → `mcp-coder gh-tool set-status <label>`

### docs/processes-prompts/development-process.md

- Find/replace all occurrences of `mcp-coder set-status` → `mcp-coder gh-tool set-status`
- This appears in the plan approval section, code review approval section, and the failure handling table.

### docs/cli-reference.md

- `set-status` is currently **not** listed as a standalone command in the CLI reference (it was already missing from the command table and command sections).
- **Add** `gh-tool set-status` to the "GitHub Tools" table.
- **Add** a `### gh-tool set-status` section with synopsis, options, and examples (parallel to other gh-tool sections).

## ALGORITHM

```
# For each slash command file:
replace "Bash(mcp-coder set-status *)" with "Bash(mcp-coder gh-tool set-status *)"
replace "mcp-coder set-status" with "mcp-coder gh-tool set-status"

# For development-process.md:
replace all "mcp-coder set-status" with "mcp-coder gh-tool set-status"

# For cli-reference.md:
add row to GitHub Tools table
add ### gh-tool set-status section
```

## DATA

No code changes. Documentation and configuration only.

## Tests

No test changes needed — these are docs/configs. The test suite from step 1 already validates the code paths.

## LLM Prompt

```
Please read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement step 2: Update slash commands and docs for gh-tool set-status.

Key changes:
1. Update 3 slash command files: plan_approve.md, implementation_approve.md, implementation_needs_rework.md
   - Update allowed-tools frontmatter
   - Update command examples in body
2. Update docs/processes-prompts/development-process.md — find/replace all "mcp-coder set-status"
3. Update docs/cli-reference.md — add gh-tool set-status to GitHub Tools table and add command section

Run all quality checks after changes. One commit for this step.
```
