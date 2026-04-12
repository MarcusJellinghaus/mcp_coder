# Step 2: Delete formatters package and update configs

**Commit message:** `refactor: delete formatters package and update configs`

**Context:** See `pr_info/steps/summary.md` for full issue context (#737).

## Goal

Delete the entire `src/mcp_coder/formatters/` package and `tests/formatters/`
directory. Then remove all `mcp_coder.formatters` references from architectural
boundary configs and documentation so that lint_imports, tach, and all other
checks pass.

## WHERE — Files to delete

### Source (6 files)
- `src/mcp_coder/formatters/__init__.py`
- `src/mcp_coder/formatters/black_formatter.py`
- `src/mcp_coder/formatters/isort_formatter.py`
- `src/mcp_coder/formatters/config_reader.py`
- `src/mcp_coder/formatters/models.py`
- `src/mcp_coder/formatters/utils.py`

### Tests (9 files)
- `tests/formatters/__init__.py`
- `tests/formatters/test_black_formatter.py`
- `tests/formatters/test_isort_formatter.py`
- `tests/formatters/test_config_reader.py`
- `tests/formatters/test_models.py`
- `tests/formatters/test_utils.py`
- `tests/formatters/test_main_api.py`
- `tests/formatters/test_debug.py`
- `tests/formatters/test_integration.py`

## WHERE — Files to modify

1. `.importlinter` — remove 2 contracts + refs in 2 others
2. `tach.toml` — remove formatter module + `depends_on` refs
3. `tools/tach_docs.py` — remove from diagram + module list
4. `docs/architecture/architecture.md` — remove formatter section
5. `pyproject.toml` — remove `formatter_integration` marker definition

## WHAT — Specific edits

### 1. `.importlinter`

**Remove entire contracts:**
- `[importlinter:contract:domain_services]` — "Domain Services Independence"
  (was LLM vs Formatters independence; only 2 modules, one deleted)
- `[importlinter:contract:formatter_implementations]` — "Formatter Implementations
  Independence" (black_formatter vs isort_formatter; both deleted)

**Keep these contracts as guardrails:**
- `[importlinter:contract:black_isolation]` — KEEP (prevents future direct black imports)
- `[importlinter:contract:isort_isolation]` — KEEP (prevents future direct isort imports)

**Edit existing contracts:**
- `[importlinter:contract:layered_architecture]`: Remove `mcp_coder.formatters`
  from the layers line:
  `mcp_coder.llm | mcp_coder.formatters | mcp_coder.prompt_manager`
  → `mcp_coder.llm | mcp_coder.prompt_manager`
- `[importlinter:contract:test_module_independence]`: Remove `tests.formatters`
  from modules list

**Update comments:**
- Layered architecture comment: remove "formatters" from the description line
  `cli -> workflows -> llm/formatters -> utils -> config`
  → `cli -> workflows -> llm -> utils -> config`

### 2. `tach.toml`

**Remove entire module block:**
```toml
[[modules]]
path = "mcp_coder.formatters"
layer = "domain"
...
```

**Remove `{ path = "mcp_coder.formatters" }` from `depends_on` in:**
- `mcp_coder.cli`
- `mcp_coder.workflows`
- `mcp_coder.workflow_utils`
- `tests` module

**Remove commented-out `tests.formatters` rule** (in the commented section near
bottom of file).

**Update comments** that mention "Formatters" in domain layer description.

### 3. `tools/tach_docs.py`

**Remove from `modules` list** (~line 259):
- `"src/mcp_coder/formatters"` entry

**Remove from hardcoded mermaid diagram** in `generate_graph_html()`:
- Node: `formatters[mcp_coder.formatters]`
- All edges referencing `formatters`:
  - `cli --> formatters`
  - `workflows --> formatters`
  - `workflow_utils --> formatters`
  - `formatters --> utils`
  - `formatters --> config`
  - `formatters --> constants`
- Style: `style formatters fill:#45b7d1,stroke:#333,color:#000`
- Update Domain subgraph to remove `formatters` line
- Update legend/info text: "Domain" description mentions "LLM, Formatters" — change
  to "LLM, Prompts" or just "LLM"

### 4. `docs/architecture/architecture.md`

**Remove lines ~269-272** — the "Code Quality & Formatting" section:
```markdown
### Code Quality & Formatting (`src/mcp_coder/formatters/`)
- **Formatter integration**: `formatters/` - Black, isort automation (tests: ...)
- **Configuration reading**: `formatters/config_reader.py` - Tool settings (tests: ...)
```

**Also remove the "formatter_integration" marker description** (around lines 356-358,
not just lines 269-272).

### 5. `pyproject.toml`

- Remove `formatter_integration` marker definition from `[tool.pytest.ini_options]`
  markers list
- Remove formatter-related marker references in the `filterwarnings` or comment
  sections of `pyproject.toml`

## ALGORITHM — No new logic

All edits are file deletions, removals, or text substitutions in config/doc files.

## DATA — No data changes

## Verification (full suite)

```
mcp__tools-py__run_pytest_check   (unit tests, exclude integration)
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
mcp__tools-py__run_lint_imports_check
mcp__tools-py__run_vulture_check
```

**Final grep verification** — confirm zero references remain:
- `mcp_coder.formatters` — nowhere in repo (except git history)
- `get_formatter_config` — nowhere in repo
- `check_line_length_conflicts` — nowhere in repo (except mcp-tools-py library)
