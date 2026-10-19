
# Step 2 — Rewrite the type-stub documentation in config.md

See `pr_info/steps/summary.md` for full context. Depends on step_1.md having
already landed (the behavior this step documents must already be true in code).

**LLM prompt:** Read `pr_info/steps/summary.md` and this file in full before making
any change. Implement exactly what is specified below for issue #1243, step 2 of 2.
Produce exactly one commit, docs only.

## Precondition check (do this first)

Open `docs/configuration/config.md` and verify it still contains, verbatim:

- The bullet `- Syncs dependencies using \`uv sync --extra dev\`` under
  "#### 2. Environment Setup".
- The line `uv sync --extra dev` inside the "### Test Command Script" fenced
  code block.
- A section heading `### Why Type Stubs Need Separate Installation`.
- The diagram line `│ 1. uv sync --inexact --extra types (in repo/)` under
  "### Two-Environment Model".

If any of these four are missing or worded differently than above (the doc has
drifted since this plan was written), **write one line to
`pr_info/.blocked.txt` and stop.** Do not improvise a rewrite against
unexpected content.

## WHERE

`docs/configuration/config.md` only. No code files. No tests apply (this is a
documentation-only change; TDD does not apply here).

## WHAT

Two edits in the same file, both required before this step's commit:

### Edit A — "Test Command Script" section (~lines 793–848)

Remove the bullet `- Syncs dependencies using \`uv sync --extra dev\`` from the
"#### 2. Environment Setup" list (the list keeps its other two bullets about
`MCP_CODER_PROJECT_DIR` and `MCP_CODER_VENV_DIR`).

Remove the line `uv sync --extra dev` from the `### Test Command Script` fenced
`bash` code block (the `# Environment setup` comment and the two `export` lines
above it stay — they are still accurate and out of this issue's scope).

### Edit B — "Why Type Stubs Need Separate Installation" section (~lines 854–905)

Replace the diagram arrow label, the "Why Type Stubs Need Separate
Installation" section, and the "Configuring Your Project for Automated
Workflows" section with the text below, verbatim (adjust only the surrounding
heading markup if the file's current heading levels differ from what the
precondition check found):

```markdown
### Two-Environment Model

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│  Execution Environment (VENV_BASE_DIR/.venv)                │
│  Pre-provisioned: mcp-coder, mcp-tools-py,                  │
│  mcp-workspace, claude CLI, pytest, mypy, pylint            │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ mcp-coder install --use-sync (in repo/)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Project Environment (repo/.venv)                           │
│  Per-run: project dependencies + type stubs, per the        │
│  target repo's own [tool.mcp-coder.install] extras          │
└─────────────────────────────────────────────────────────────┘
\`\`\`

### Why Type Stubs Are the Target Repo's Responsibility

The MCP tools-py server runs mypy against **project code** using the
**project's virtual environment**. For mypy to resolve types correctly, type
stub packages (e.g., \`types-requests\`, \`types-tabulate\`) must be installed
in the project's \`.venv\`, not the execution environment.

There is no separate per-run sync step for this. The Jenkins provisioning step
(\`mcp-coder install --source local --local-path <repo> --use-sync --refresh\`)
installs the target repo and its dependencies in one pass, honoring both
\`[tool.mcp-coder.install-from-github]\` overrides and the target repo's own
\`[tool.mcp-coder.install] extras\`. Whatever extras that setting names —
including \`types\`, if the target repo defines one — are installed then;
nothing afterwards re-syncs or reverts that result.

### Configuring Your Project for Automated Workflows

If your project uses mcp-coder workflows and wants type stubs installed
automatically, add a \`types\` extra to its own \`pyproject.toml\` and reference
it from \`[tool.mcp-coder.install]\`:

\`\`\`toml
[project.optional-dependencies]
types = [
    "types-requests>=2.28.0",
    # Add other type stubs your project needs
]

[tool.mcp-coder.install]
extras = "types"  # or e.g. "dev" if dev already includes types
\`\`\`

Without \`types\` named there, \`mcp-coder install\` will not install type
stubs and mypy will degrade gracefully (no error) rather than fail.
```

## HOW

Plain markdown edit via the file-editing MCP tool — no imports, no decorators,
no integration points. After editing, re-read the file to confirm no stray
reference to `uv sync --inexact --extra types` or `uv sync --extra dev`
remains anywhere in `docs/configuration/config.md`.

## ALGORITHM

Not applicable — this step has no executable logic.

## DATA

Not applicable — this step produces no return values or data structures. Stage
and commit `docs/configuration/config.md` alone in one commit.
