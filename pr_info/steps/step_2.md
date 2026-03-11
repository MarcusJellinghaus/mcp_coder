# Step 2: Add Documentation Structure to repository-setup.md

> **Context**: See [summary.md](summary.md) for full issue overview.

## LLM Prompt

Add documentation structure guidance to `docs/repository-setup.md`. This involves two edits:
1. Add a checklist item to the Quick Setup Checklist
2. Add an "Architecture Documentation" section in Mandatory Setup, after the "Claude Code Configuration" section

Use mcp-coder's own `docs/` folder as the reference example. Keep it concise — the folder tree with inline annotations is enough. See step details below for exact placement and content.

## WHERE

- **File**: `docs/repository-setup.md`
- **Location 1**: Quick Setup Checklist (after the "Test workflow" item, ~line 29)
- **Location 2**: Mandatory Setup, after "Claude Code Configuration" section ends (before the `---` separator to Optional Setup, ~line 270)

## WHAT

Two insertions into an existing Markdown file — no functions, no signatures.

### Edit A — Checklist item

Add after the last existing checklist item (`- [ ] Test workflow with a sample issue`):

```markdown
- [ ] Create `docs/architecture/architecture.md` (required by `/implementation_review`)
```

### Edit B — New section before Optional Setup

Add a new section titled "## Architecture Documentation" containing:
- One-sentence explanation of why it's mandatory (dependency from `/implementation_review`)
- One-sentence note that architecture docs improve LLM codebase navigation
- The recommended folder tree with `(mandatory)` annotation on `architecture.md`
- A one-liner pointing to mcp-coder's own `docs/` as a reference example

**Content to insert** (before the `---` / `# Optional Setup` separator):

```markdown
## Architecture Documentation

The `/implementation_review` command checks code against `docs/architecture/architecture.md`. This file must exist for code reviews to work. Architecture documentation also enables LLM-assisted codebase navigation.

### Recommended Structure

```
docs/
├── README.md
├── architecture/
│   ├── architecture.md                    (mandatory - used by /implementation_review)
│   ├── architecture-maintenance.md
│   └── dependencies/
│       ├── readme.md
│       ├── dependency_graph.html          (generated)
│       ├── pydeps_graph.html              (generated)
│       └── pydeps_graph.dot               (generated)
└── [project-specific docs]
```

**Reference:** See this repository's own [`docs/`](.) folder for a working example of this structure.
```

## HOW

- Direct Markdown edits — two insertions into existing document
- No imports, no decorators, no integration points

## ALGORITHM

```
1. Open docs/repository-setup.md
2. Find the Quick Setup Checklist, append one checklist item
3. Find the "---" separator before "# Optional Setup"
4. Insert "Architecture Documentation" section before that separator
5. Save
```

## DATA

- **Input**: Existing `repository-setup.md` without documentation guidance
- **Output**: Updated `repository-setup.md` with checklist item and architecture docs section
- **Verification**: The section references `docs/architecture/architecture.md` which exists in the repo; the folder tree matches the actual repo structure

## TDD

Not applicable — Markdown-only change with no testable behavior.
