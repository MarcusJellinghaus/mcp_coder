# Step 5 — Cut down `python.md` *Architecture Enforcement*, fix the MCP note

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_5.md` exactly.
> Keep the headings `## Architecture Enforcement` and `### Dependency Declaration Hygiene`
> (the #1181 hub links to them). Make one commit.

## WHERE
`docs/repository-setup/python.md`: `## Architecture Enforcement` (about lines 79–178) and the
`> **For Claude Code:**` note under `### Quality Check Tools` (about lines 220–221).

## WHAT — resulting `## Architecture Enforcement`

```
## Architecture Enforcement

> Overview: see [quality-and-security-checks.md](quality-and-security-checks.md).

Why the architecture is enforced, and which tool guards what: see
[enforcement.md](../architecture/enforcement.md).

### Import Architecture Enforcement
> **Customize (`.importlinter`):** Package names and contract definitions.

### Dependency Architecture Validation
> **Customize (`tach.toml`):** Module boundaries for your package.

### Dead Code Elimination
> **Customize (`vulture_whitelist.py`):** Project-specific false positives.

### Dependency Declaration Hygiene
> **Customize (`[tool.deptry]` in `pyproject.toml`):** ... (existing three-line note, unchanged)
```

## HOW
- Delete the intro paragraph, `### Why Architecture Enforcement?` and `### Running Architecture Tools`.
- In each `###` subsection keep only the `> **Customize ...**` note. Delete the **Tool:** blocks
  (including pycycle) and the deptry "Runs against `src` only" paragraph.
- **MCP note** under *Quality Check Tools*: replace both lines with
  `> **For Claude Code:** Use MCP tools where available: `mcp__mcp-tools-py__run_lint_imports_check`, `mcp__mcp-tools-py__run_tach_check`, `mcp__mcp-tools-py__run_vulture_check`, `mcp__mcp-tools-py__run_deptry_check`, `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`.`
  `> Shell scripts are for human developers and CI pipelines. `pycycle_check.sh` has no MCP equivalent — run it via Bash when needed.`
- Leave `## CI Workflow for Python` and everything else untouched.

Precondition: if #1351 has already fixed the MCP note on `main`, leave it as it is. That is not a blocker.

## ALGORITHM
None.

## DATA
None.

## Checks
- `search_files(pattern="^## Architecture Enforcement$|^### Dependency Declaration Hygiene$", glob="docs/repository-setup/python.md")` finds both.
- `search_files(pattern="python.md#", glob="docs/**/*.md")`: every anchor still exists.

## Commit
`docs(repository-setup): point python.md architecture section at enforcement.md`
