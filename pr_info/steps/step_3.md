# Step 3 — Context-root finder + reporter

**Depends on:** Step 1 (`claude_md_paths`), Step 2 (`project_dir` parameter).

**Goal:** make the agent's rule source visible. This is the durable half of #1113 — without it
the next drift is equally silent, exactly as this one was from December onward.

Requirement 5 of the issue. Reports at `OUTPUT` level, once per run.

---

## WHERE

- `src/mcp_coder/cli/utils.py` — two new functions, plus one call inside `resolve_execution_dir`
- `tests/cli/test_utils.py` — new test class

## WHAT

```python
def find_context_claude_md(start: Path) -> list[Path]:
    """Find the CLAUDE.md files Claude's cwd-upward walk would reach first.

    Walks from ``start`` to the filesystem root and returns every existing
    candidate at the NEAREST ancestor level that has any. Not a complete account
    of Claude's memory chain: no ~/.claude/CLAUDE.md, no @import expansion.

    Returns:
        Resolved paths at the nearest level with a hit, or [] if none exist.
    """


def report_context_root(execution_dir: Path, project_dir: str | Path | None) -> None:
    """Log the Claude working directory and the project instructions in effect.

    Logs at OUTPUT level. Warns when a resolved file lies outside project_dir.
    """
```

Both public; both added to `__all__`. `find_context_claude_md` is separate from
`report_context_root` because `verify.py` (Step 5) needs the *data*, not the log lines.

## HOW

- New imports in `cli/utils.py`:
  `from ..prompts.prompt_loader import claude_md_paths` and
  `from ..utils.log_utils import OUTPUT`.
  No cycle: `prompt_loader` imports only `utils.data_files` and `utils.pyproject_config`, and
  `cli/commands/verify.py` already imports `prompt_loader`. Still run
  `run_lint_imports_check` and `run_tach_check`.
- **Wiring:** call `report_context_root(resolved, project_dir)` inside `resolve_execution_dir`,
  immediately before each `return`, on **both** branches (default and explicit
  `--execution-dir`). One wiring point covers all nine commands and makes it structurally
  impossible for a call site to forget — the same argument the issue makes for putting the
  deprecation warning here. See summary.md §3 for why this departs from "called next to each
  `resolve_execution_dir`".
- Deliberately **not** `log_command_startup` — only 4 of the 9 commands call it and it logs at
  `info`.

## ALGORITHM

```
# find_context_claude_md
current = start.resolve()
while True:
    hits = [p.resolve() for p in claude_md_paths(current) if p.exists()]
    if hits: return hits                       # nearest level wins, return ALL of them
    if current.parent == current: return []    # filesystem root reached
    current = current.parent
```

```
# report_context_root
log(OUTPUT, "Claude working directory: %s", execution_dir)
hits = find_context_claude_md(execution_dir)
if not hits:
    log(OUTPUT, "<label>: none found")
    return
for h in hits: log(OUTPUT, "<label>: %s", h)
if project_dir is None: return
root = Path(project_dir).resolve()
for h in hits:
    if not h.is_relative_to(root):
        logger.warning("Project instructions file lies outside the project directory: "
                       "%s (project: %s) — the driven project's rules may not reach the agent", h, root)
```

Wrap the walk in `try/except OSError` and return `[]` — mirrors the guard in `is_claude_md`
(`prompt_loader.py:163-164`); a permission error mid-walk must not crash a workflow.

### Two rules that carry design intent

1. **Every hit at the nearest level, never one picked by precedence.** When a directory holds
   both `CLAUDE.md` and `.claude/CLAUDE.md`, report both. The order inside `claude_md_paths` is
   a membership list, not a precedence rule; treating it as precedence would invent a fact.
2. **Word the label so it does not claim completeness.** Something like
   `"Project instructions (Claude cwd walk):"` — never "Claude's memory files", which would
   imply `~/.claude/CLAUDE.md` and `@import` expansion are covered. They are not.

## DATA

- `find_context_claude_md` → `list[Path]`, resolved, `[]` when nothing exists anywhere up the
  chain. Length 1 or 2 in practice.
- `report_context_root` → `None`. Side effect only: one `OUTPUT` line for the cwd, one `OUTPUT`
  line per hit (or one "none found"), zero or more `WARNING` lines.

## TESTS (write first)

New `class TestContextRootReporting` in `tests/cli/test_utils.py`.

**`find_context_claude_md`**
1. Root-level only: `<d>/CLAUDE.md` exists → `[<d>/CLAUDE.md]`.
2. `.claude/` only: → `[<d>/.claude/CLAUDE.md]`.
3. **Both at one level → both returned, length 2.** Pins rule 1 above.
4. Nearest level wins: parent and child both have `CLAUDE.md` → only the child's is returned.
5. Found in an ancestor when the start directory has none.
6. Nothing anywhere → `[]` (use a `tmp_path` subtree; assert `== []` rather than asserting on
   real ancestors of `tmp_path`, which are outside the test's control).

**`report_context_root`** (`caplog.set_level(OUTPUT)`)

7. Logs the working directory.
8. Logs each hit when two exist at one level.
9. Logs an explicit "none found" when there are none.
10. **Warns when a hit lies outside `project_dir`** — build `tmp_path/"tool_env"/CLAUDE.md` and
    pass `project_dir=tmp_path/"repo"` (no CLAUDE.md). This is the December scenario; assert
    `WARNING` level.
11. Does **not** warn when the hit is inside `project_dir`.
12. Does not warn when `project_dir is None`.

**Wiring**

13. `resolve_execution_dir(None, project_dir=tmp_path)` produces the working-directory
    `OUTPUT` line — proves the resolver reports on the default branch.
14. `resolve_execution_dir(str(tmp_path))` also produces it — proves it reports on the explicit
    branch too.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
mcp__tools-py__run_lint_imports_check
mcp__tools-py__run_tach_check
```

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Report the Claude working directory and project instructions in effect (#1113)

find_context_claude_md walks cwd upward and returns every CLAUDE.md at the
nearest ancestor level that has any; report_context_root logs them at OUTPUT
and warns when one lies outside project_dir. Called from resolve_execution_dir
so all nine commands report without per-site wiring.

Scope is the cwd walk only - not ~/.claude/CLAUDE.md, not @import expansion.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially "3. Observability becomes a first-class concern"
> and "5. What the report does and does not claim") and `pr_info/steps/step_3.md`, then
> implement Step 3.
>
> Add two public functions to `src/mcp_coder/cli/utils.py` and register them in `__all__`:
> `find_context_claude_md(start: Path) -> list[Path]` and
> `report_context_root(execution_dir: Path, project_dir: str | Path | None) -> None`.
> Use `claude_md_paths` from Step 1 and the `OUTPUT` level from
> `mcp_coder.utils.log_utils`. Follow the ALGORITHM pseudocode in the step file, including the
> `try/except OSError` guard.
>
> Two rules matter more than they look:
> (a) at the nearest ancestor level that has any hit, return/report **every** hit there — never
> pick one by precedence; (b) word the log label so it does not claim to be a complete account
> of Claude's memory chain (no `~/.claude/CLAUDE.md`, no `@import` expansion are covered).
>
> Wire it by calling `report_context_root(resolved, project_dir)` from inside
> `resolve_execution_dir`, before the return, on **both** branches. Do not add per-call-site
> wiring and do not put it in `log_command_startup`.
>
> Follow TDD: write the fourteen tests listed under TESTS in a new
> `class TestContextRootReporting` in `tests/cli/test_utils.py` first, watch them fail, then
> implement. Test 10 (warning when a hit lies outside `project_dir`) reproduces the December
> Jenkins scenario — make sure it genuinely fails before the implementation exists.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md), `run_mypy_check`,
> `run_lint_imports_check` and `run_tach_check`. Fix everything before finishing. One commit.
