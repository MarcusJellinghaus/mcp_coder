# Step 2 — Toolkit-neutral prose in every deployed `.claude/` file

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`). Implement
> step 2 only: write the new test first (it fails), then neutralise the prose, extend
> `python.md`, sync the rebase row and retarget `test_prompt.py`. Never edit frontmatter
> (`tools:`, `allowed-tools`, `skills:`, `hooks:`). Run the format, pylint, pytest (fast unit
> tests) and mypy checks from `.claude/CLAUDE.md`; all must pass. One commit:
> `docs(claude): make deployed skills, agents and knowledge base toolkit-neutral`.

## WHERE

- New: `tests/cli/commands/test_init_deployed_neutral.py`
- `tests/workflows/rebase/test_prompt.py`
- `.claude/knowledge_base/{python,planning_principles,refactoring_principles}.md`
- `.claude/agents/{code-engineer,plan-engineer}.md` (bodies)
- `.claude/skills/*/SKILL.md` listed below (bodies), `.claude/skills/rebase/rebase_design.md`
- `src/mcp_coder/prompts/prompts.md` (Rebase Conflict Resolution table)

## WHAT — the new test

```python
# tests/cli/commands/test_init_deployed_neutral.py
"""Deployed .claude/ prose must not name Python tools or conventions.""" (module docstring:
say init copies these files into every repo; Python specifics belong in python.md,
which only mcp-tools-py repos get.)

REPO_ROOT = Path(__file__).resolve().parents[3]
EXEMPT = Path("knowledge_base") / "python.md"
TERMS = ("pylint", "pytest", "mypy", "ruff", "vulture", "lint-imports", "lint_imports",
         "import-linter", "tach", "tools-py", "run_format_code", "move_symbol",
         "move_module", "pyproject", "uv.lock", "TYPE_CHECKING", "python")
_TERM_RE = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(map(re.escape, TERMS)) + r")(?![a-z0-9])"
    r"|\.py(?![a-z0-9])",
    re.IGNORECASE,
)

def _python_terms(text: str) -> list[str]: return _TERM_RE.findall(text) ... (the matched strings)
def _prose(path: Path) -> str: return frontmatter.load(path).content   # whole file if no frontmatter
def test_matcher() -> None: ...
def test_deployed_prose_is_toolkit_neutral() -> None: ...
```

ALGORITHM (`test_deployed_prose_is_toolkit_neutral`):
```
base = REPO_ROOT / ".claude"
files = sorted(p for sub in DEPLOY_SUBDIRS for p in (base / sub).rglob("*.md")
               if p.relative_to(base) != EXEMPT)
assert files
offenders = [f"{rel}:{lineno}: {hits}" for each file, for each prose line with hits]
assert not offenders, "...move Python specifics to knowledge_base/python.md:\n" + lines
```

`test_matcher` asserts: `mcp__mcp-tools-py__run_pytest_check` hits; `"attach"` and
`"detach"` don't; `` `types.py` `` hits; `".pyc"` doesn't; `"Python"` hits (case).

## WHAT — `tests/workflows/rebase/test_prompt.py`

`_skill_strategy_rows` reads `REPO_ROOT / ".claude" / "skills" / "rebase" / "SKILL.md"`
(`REPO_ROOT = Path(__file__).resolve().parents[3]`) instead of `find_data_file(...)`; drop
the `find_data_file` import; say "repo-root" instead of "packaged" in the docstrings. Row
prefixes `| Code files`, `| Test files`, `| Config files` stay.

## WHAT — prose edits (bodies only)

Wording below is the target; small rephrasing is fine as long as the meaning stays and the
test passes. Every Python detail removed must land in `python.md` (last section).

### Knowledge base
- `planning_principles.md`
  - "Ideally each step can be completed such that pylint/pytest/mypy still pass afterward."
    → "…such that the project's checks and tests still pass afterward."
  - Test-structure bullet → "**Test structure mirrors source structure.** One test file per
    module, at the matching path under the test folder."
- `refactoring_principles.md`
  - Key Rules: "**Use the refactoring tools** (`move_symbol`, `move_module`)…" → "**Use the
    project's refactoring tools** (move a symbol or a module) — they update imports…"
  - Allowed edits: "including optional-import guards"; "Package and test-setup files needed
    by the move — no re-exports kept for backward compatibility".
  - Plan the layout, import cycles → "**Import cycles:** keep the lazy import on one side and
    a type-only import on the other. A runtime value both sides need (e.g. a named tuple)
    goes into a dependency-free module such as a types module."
  - Verify: "test count, test markers or tags, mock targets that still resolve but replace
    nothing, shared test setup no longer applied, names shadowed in the destination"; "Run
    all checks — the project's checks and tests, architecture checks, file size."

### Agents (body only)
- `code-engineer.md` Fix bullet: "Then run the checks CLAUDE.md lists (format, then the
  checks and tests)."
- `plan-engineer.md`: "**Requirement changes** (dependency manifest, checker config, other
  config)".

### Skills (body only)
- `commit_push` step 1: "Format all code with the project's formatter, as CLAUDE.md maps it."
- `implement_direct` step 5 → "Run the project's checks and tests as CLAUDE.md maps them,
  with the arguments it requires — fix all issues and failures." Step 6 → as `commit_push`.
- `implementation_finalise` §3 → one bullet: "Run the project's checks and tests as CLAUDE.md
  maps them (fix all errors and failures)".
- `implementation_review`: "do not use pylint warnings" → "do not report linter warnings".
- `implementation_review_supervisor`
  - Setup 2 → "Read every file under `.claude/knowledge_base/` (`*.md`)." Delete the
    now-redundant "**Additional context:** … `refactoring_principles.md`" line.
  - Workflow 8 → "Run the project's dead-code and architecture checks yourself, as CLAUDE.md
    and the knowledge base map them (skip if the project has none). Escalate architecture
    violations to the user; for simple dead-code false positives, launch `code-engineer` to
    fix them, then re-run until clean."
  - Agent instructions parenthesis: "…; run tests with the arguments CLAUDE.md requires; no
    `cd` prefix; approved commands only".
  - Escalation: "Import contract or architecture violations (from the architecture checks):
    escalate…".
- `plan_review`: "flag new dependencies (the dependency manifest) that should be applied
  during planning…".
- `plan_review_supervisor`: "config changes (e.g. the dependency manifest, checker
  configuration)"; "…with the updated development environment."
- `pr_comment_triage`
  - Trust list: "`.github/`; dependencies, extras or check configuration in the dependency
    manifest; `.claude/`, `CLAUDE.md`, `.mcp.json`; architecture-check config; anything
    touching secrets or tokens."
  - Fix bullet: "change code, run quality checks (format, then the checks and tests
    CLAUDE.md maps), commit and push, …".
  - Clean-tree step 1 → "Any tracked or untracked change → stop and report the uncommitted
    changes."
- `implementation_approve`, `implementation_needs_rework`, `plan_approve`: clean-tree line
  → "Any tracked or untracked change → stop and report the uncommitted changes."
- `rebase/SKILL.md`: Workflow 5 → "Run the project's checks and tests as CLAUDE.md maps
  them". Strategy row → `| Code files | Keep both sides, merge imports |`.
- `rebase/rebase_design.md`: "(filesystem, tools-py, etc.)" → "(filesystem, language tools,
  etc.)".

### `src/mcp_coder/prompts/prompts.md`
Rebase Conflict Resolution table: `| Code files (`.py`, `.js`, etc.) | …` →
`| Code files | Keep both sides, merge imports |` (identical to `SKILL.md`).

### `knowledge_base/python.md` (exempt from the test) — target content
```
# Python Guidelines

For repos with the `mcp-tools-py` toolkit. Skills and agents name steps by purpose; here
they map to these tools.

## Tools by purpose
- **Checks:** pylint, mypy, ruff (`run_pylint_check`, `run_mypy_check`, `run_ruff_check`).
- **Tests:** pytest (`run_pytest_check`), with the arguments and marker filters CLAUDE.md requires.
- **Format:** `run_format_code`.
- **Dead code and architecture:** vulture (`run_vulture_check`), import-linter
  (`run_lint_imports_check`), tach (`run_tach_check`). The implementation-review supervisor
  runs vulture and lint-imports itself before its final status: import-contract violations
  go to the user (fixes may move code between layers); simple vulture whitelist additions go
  to `code-engineer`, then re-run until clean.
- **Refactoring:** `move_symbol`, `move_module` (they update imports), `rename_symbol`.

## Conventions
- (keep the four existing bullets: f-strings, type hints, no conditional imports, skip not fake)
- **Test layout:** tests for `src/foo/bar.py` go in `tests/foo/test_bar.py`.
- **Config names:** the dependency manifest is `pyproject.toml` (dependencies, extras,
  `[tool.*]` check config such as mypy overrides); architecture-check config is
  `.importlinter` and `tach.toml`. Apply requirement changes during planning so
  implementation starts in the updated Python environment.

## Refactoring
- Allowed edits in a pure move include `try/except ImportError` optional-import blocks and
  the `__init__.py` / `conftest.py` files the move needs.
- Import cycles: pylint `R0401` counts function-local imports as edges, but not
  `if TYPE_CHECKING:` imports. A shared runtime value (e.g. a NamedTuple) goes in a
  dependency-free module such as `types.py`.
- Verifying a pure move: pytest test count and markers, `patch` targets that resolve but
  patch nothing, fixtures no longer applied.
```

## DATA

- `_python_terms(text) -> list[str]` — matched substrings, empty when neutral.
- No production-code changes in this step besides `prompts.md`.

## Constraints

- `tests/icoder/test_repo_agents.py` and `tests/icoder/test_repo_skills.py` must pass
  unchanged (frontmatter untouched).
- `tests/cli/commands/test_init_deployed_paths.py` must still pass: new prose names no
  `docs/...` path.
- `tests/prompts/test_prompts_toolkit_neutral.py` must still pass.
- If the neutral test can only pass by editing frontmatter, write one line to
  `pr_info/.blocked.txt` and stop.
