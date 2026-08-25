# Step 3 — Context-root finder + reporter

**Depends on:** Step 1 (`claude_md_paths`), Step 2 (`project_dir` parameter).

**Goal:** make the agent's rule source visible. This is the durable half of #1113 — without it
the next drift is equally silent, exactly as this one was from December onward.

Requirement 5 of the issue. Reports at `OUTPUT` level, once per run.

---

## WHERE

- `src/mcp_coder/cli/utils.py` — three new functions, plus one call inside
  `resolve_execution_dir`
- `tach.toml` — allow `mcp_coder.cli` → `mcp_coder.prompts` (see HOW)
- `tests/cli/test_utils.py` — new test class

## WHAT

```python
def find_context_claude_md(start: Path, stop_at: Path | None = None) -> list[Path]:
    """Find the CLAUDE.md files Claude's cwd-upward walk would reach first.

    Walks from ``start`` upward and returns every existing candidate at the
    NEAREST ancestor level that has any. Not a complete account of Claude's
    memory chain: no ~/.claude/CLAUDE.md, no @import expansion.

    Args:
        start: Directory to start the walk from.
        stop_at: Last directory to examine, inclusive. ``None`` (production
            default) walks to the filesystem root.

    Returns:
        Resolved paths at the nearest level with a hit, or [] if none exist.
    """


def is_outside_project_dir(path: Path, project_dir: str | Path | None) -> bool:
    """Return True when ``path`` does not lie inside ``project_dir``.

    The single definition of "outside" shared by the run-time report and the
    verify report. Always False when project_dir is None - with no anchor there
    is nothing to be outside of.
    """


def report_context_root(execution_dir: Path, project_dir: str | Path | None) -> None:
    """Log the Claude working directory and the project instructions in effect.

    Logs at OUTPUT level. Warns when a resolved file lies outside project_dir.
    """
```

All three public; all three added to `__all__`. `find_context_claude_md` is separate from
`report_context_root` because `verify.py` (Step 5) needs the *data*, not the log lines.

**`is_outside_project_dir` is the shared predicate.** Step 5's verify rows use the *same*
function to pick the warning marker. Specifying the comparison twice would let the run-time
report and the verify report drift on the one rule the issue calls load-bearing.

**`stop_at` exists so the walk is testable.** Production callers pass nothing and walk to the
root; tests pass `stop_at=tmp_path` so a "nothing found anywhere" assertion cannot be falsified
by a `CLAUDE.md` sitting in a real ancestor of the temp directory (on a developer machine,
`$HOME` plausibly has one). It is a boundary parameter, not a feature — do not thread it
through `resolve_execution_dir` or `verify.py`.

## HOW

- New imports in `cli/utils.py`:
  `from ..prompts.prompt_loader import claude_md_paths` and
  `from ..utils.log_utils import OUTPUT`.
  No cycle: `prompt_loader` imports only `utils.data_files` and `utils.pyproject_config`, and
  `cli/commands/verify.py` already imports `prompt_loader`. Still run
  `run_lint_imports_check` and `run_tach_check`.
- **`tach.toml` needs one line.** The `[[modules]] path = "mcp_coder.cli"` block lists its
  allowed dependencies and **does not currently include `mcp_coder.prompts`** — check it: the
  block runs from `mcp_coder` through `mcp_coder.services`. Add:
  ```toml
      { path = "mcp_coder.prompts" },      # CLAUDE.md candidate locations for context reporting
  ```
  Do this in *this* step, in the same commit as the import. That `verify.py` already imports
  `prompt_loader` says the *direction* is sound (`presentation` → `domain`, which the layer
  order permits); it does not mean the dependency is on the module's allowlist. Run
  `run_tach_check` and confirm it passes before committing. If tach reports the dependency was
  already permitted, drop the `tach.toml` edit rather than leaving a redundant entry.
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
boundary = stop_at.resolve() if stop_at is not None else None
while True:
    hits = [p.resolve() for p in claude_md_paths(current) if p.exists()]
    if hits: return hits                       # nearest level wins, return ALL of them
    if boundary is not None and current == boundary: return []   # test boundary reached
    if current.parent == current: return []    # filesystem root reached
    current = current.parent
```

The boundary check sits **after** the hit check, so `stop_at` is examined inclusively: a
`CLAUDE.md` in the boundary directory itself is still found.

```
# is_outside_project_dir
if project_dir is None: return False
return not path.resolve().is_relative_to(Path(project_dir).resolve())
```

```
# report_context_root
log(OUTPUT, "Claude working directory: %s", execution_dir)
hits = find_context_claude_md(execution_dir)
if not hits:
    log(OUTPUT, "<label>: none found")
    return
for h in hits: log(OUTPUT, "<label>: %s", h)
for h in hits:
    if is_outside_project_dir(h, project_dir):
        logger.warning("Project instructions file lies outside the project directory: "
                       "%s (project: %s) — the driven project's rules may not reach the agent",
                       h, project_dir)
```

Wrap the walk in `try/except OSError` and return `[]` — mirrors the guard in `is_claude_md`
(`prompt_loader.py:163-164`); a permission error mid-walk must not crash a workflow.
`is_outside_project_dir` gets the same guard: on `OSError` from `.resolve()`, return `False`
(do not warn on a path we could not resolve).

### Two rules that carry design intent

1. **Every hit at the nearest level, never one picked by precedence.** When a directory holds
   both `CLAUDE.md` and `.claude/CLAUDE.md`, report both. The order inside `claude_md_paths` is
   a membership list, not a precedence rule; treating it as precedence would invent a fact.
2. **Word the label so it does not claim completeness.** Something like
   `"Project instructions (Claude cwd walk):"` — never "Claude's memory files", which would
   imply `~/.claude/CLAUDE.md` and `@import` expansion are covered. They are not.

## Expected impact on existing tests

Wiring the report into `resolve_execution_dir` means **every** existing call now emits two or
more `OUTPUT` records and walks the filesystem from the resolved directory to the root. Same
style of enumeration as Step 2's warning analysis — verify each claim before relying on it.

**Unaffected: the six command sites whose tests patch the resolver.** `test_create_pr.py`,
`test_implement.py`, `test_create_plan.py`, `test_review.py`, `test_check_branch_status.py`
(`:167`, `:226`) and `test_rebase.py` (`:73`, `:107`, `:122`) all patch `resolve_execution_dir`,
so no report is produced and no walk happens.

**Three command sites do *not* patch it, so their tests execute the real resolver, the real
walk and the real logging:**

- `commit.py:74` — `tests/cli/commands/test_commit.py`, 20 calls to `execute_commit_auto`
  (`:71`, `:108`, `:151`, `:195`, `:228`, `:267`, `:285`, `:294`, `:307`, `:334`, `:365`,
  `:410`, `:819`, `:862`, `:884`, `:929`, `:1112`, `:1142`, `:1171`, `:1196`).
- `prompt.py:48` — `tests/cli/commands/test_prompt.py` (23 calls), `test_prompt_streaming.py`
  (14 calls), `tests/cli/commands/test_session_priority.py` (6 calls),
  `tests/integration/test_execution_dir_integration.py` (`:271`, `:318`, `:517`),
  `tests/integration/test_mcp_config_integration.py` (`:179`, `:242`, `:308`).
- `icoder.py:51` — `tests/icoder/test_cli_icoder.py` (19 calls), `test_cli_icoder_mcp.py` (5),
  `test_cli_icoder_resume.py` (6), `test_icoder_permission_wiring.py` (4).

**Why none of them break, and what to check if one does:**

1. **Nothing reaches stdout.** These tests call the `execute_*` functions directly; `main.py`'s
   `setup_logging` (`main.py:316-318`) never runs, so log records propagate to a root logger
   with no handler. `capsys` assertions in `test_prompt_streaming.py` — the densest
   output-asserting file here — see only `print()` output and are untouched.
2. **No test asserts on a record count.** Grep confirms no `len(caplog.records)`,
   `caplog.records ==` or `caplog.record_tuples` assertion exists anywhere in `tests/`, so extra
   records cannot fail an existing `caplog` test. Substring assertions (`"..." in caplog.text`)
   stay true.
3. **The walk is real I/O.** From `Path.cwd()` (the repo) it terminates at the repo's own
   `CLAUDE.md` after one level; from a `tmp_path` it walks to the root. Both are cheap, but this
   is the reason `find_context_claude_md` needs its `try/except OSError` guard rather than
   trusting the caller.
4. **A warning may now fire in `test_commit.py:1112`, `:1142`, `:1171`, `:1196`.** Those pass
   `project_dir="/repo"`, which does not exist; after Step 4 it becomes the execution dir, the
   walk from it finds nothing, and the report logs "none found". No warning, no failure — but
   if one of these four ever starts failing, this is why.

If a test *does* break, the fix is the test, not the wiring — except that a break in
`test_prompt_streaming.py`'s captured output would mean assumption 1 is wrong, which would
invalidate the whole "wire it into the resolver" decision (summary.md §3). Escalate rather than
patching around it.

## DATA

- `find_context_claude_md` → `list[Path]`, resolved, `[]` when nothing exists between `start`
  and the boundary (`stop_at`, or the filesystem root). Length 1 or 2 in practice.
- `is_outside_project_dir` → `bool`. `False` when `project_dir` is `None`.
- `report_context_root` → `None`. Side effect only: one `OUTPUT` line for the cwd, one `OUTPUT`
  line per hit (or one "none found"), zero or more `WARNING` lines.

## TESTS (write first)

New `class TestContextRootReporting` in `tests/cli/test_utils.py`.

**`find_context_claude_md`**
1. Root-level only: `<d>/CLAUDE.md` exists → `[<d>/CLAUDE.md]`.
2. `.claude/` only: → `[<d>/.claude/CLAUDE.md]`.
3. **Both at one level → both returned, length 2.** Pins rule 1 above.
4. Nearest level wins: parent and child both have `CLAUDE.md` → only the child's is returned.
5. Found in an ancestor when the start directory has none — start at `tmp_path/"a"/"b"`, put the
   file at `tmp_path/"a"`, pass `stop_at=tmp_path`.
6. **Nothing anywhere → `[]`.** Start at `tmp_path/"a"/"b"` with no `CLAUDE.md` in the subtree
   and pass **`stop_at=tmp_path`**. Without the boundary this assertion is falsifiable by any
   `CLAUDE.md` in a real ancestor of `tmp_path` (a developer `$HOME`, a CI workspace root) —
   directories no test controls. The boundary is what makes `== []` a statement about the code
   rather than about the machine.
7. **The boundary is inclusive**: `CLAUDE.md` in `stop_at` itself is found (start below it,
   `stop_at=tmp_path`, file at `tmp_path`) → returned, not `[]`.

**`is_outside_project_dir`**

8. Hit inside `project_dir` → `False`; hit in a sibling tree → `True`; `project_dir=None` →
   `False`. Parameterize.

**`report_context_root`** (`caplog.set_level(OUTPUT)`)

9. Logs the working directory.
10. Logs each hit when two exist at one level.
11. Logs an explicit "none found" when there are none.
12. **Warns when a hit lies outside `project_dir`** — build `tmp_path/"tool_env"/CLAUDE.md` and
    pass `execution_dir=tmp_path/"tool_env"`, `project_dir=tmp_path/"repo"` (no CLAUDE.md). This
    is the December scenario; assert `WARNING` level.
13. Does **not** warn when the hit is inside `project_dir`.
14. Does not warn when `project_dir is None`.

**Wiring**

15. `resolve_execution_dir(None, project_dir=tmp_path)` produces the working-directory
    `OUTPUT` line — proves the resolver reports on the default branch.
16. `resolve_execution_dir(str(tmp_path))` also produces it — proves it reports on the explicit
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
and warns when one lies outside project_dir, using the shared
is_outside_project_dir predicate that the verify report will reuse. Called
from resolve_execution_dir so all nine commands report without per-site
wiring.

The walk takes an optional stop_at boundary so tests can assert "found
nothing" without depending on directories above tmp_path.

Scope is the cwd walk only - not ~/.claude/CLAUDE.md, not @import expansion.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially "3. Observability becomes a first-class concern"
> and "5. What the report does and does not claim") and `pr_info/steps/step_3.md`, then
> implement Step 3.
>
> Add three public functions to `src/mcp_coder/cli/utils.py` and register them in `__all__`:
> `find_context_claude_md(start: Path, stop_at: Path | None = None) -> list[Path]`,
> `is_outside_project_dir(path: Path, project_dir: str | Path | None) -> bool` and
> `report_context_root(execution_dir: Path, project_dir: str | Path | None) -> None`.
> Use `claude_md_paths` from Step 1 and the `OUTPUT` level from
> `mcp_coder.utils.log_utils`. Follow the ALGORITHM pseudocode in the step file, including the
> `try/except OSError` guards.
>
> `is_outside_project_dir` is the **single** definition of "outside" — Step 5's verify rows
> import the same function. Do not inline the comparison anywhere.
>
> `stop_at` is a walk-termination boundary that exists so tests can assert "found nothing"
> deterministically. Production callers pass nothing; do not thread it through
> `resolve_execution_dir` or `verify.py`. The boundary is inclusive — check it *after* the hit
> check.
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
> Add `{ path = "mcp_coder.prompts" }` to the `mcp_coder.cli` `depends_on` list in `tach.toml`
> in this same commit — the new `cli/utils.py` → `prompts.prompt_loader` import is not on that
> allowlist today. Run `run_tach_check` to confirm; drop the edit if tach says it was already
> permitted.
>
> Follow TDD: write the sixteen tests listed under TESTS in a new
> `class TestContextRootReporting` in `tests/cli/test_utils.py` first, watch them fail, then
> implement. Test 12 (warning when a hit lies outside `project_dir`) reproduces the December
> Jenkins scenario — make sure it genuinely fails before the implementation exists.
>
> Read the "Expected impact on existing tests" section before running the suite: the three
> command sites that do *not* patch `resolve_execution_dir` (`commit.py`, `prompt.py`,
> `icoder.py`) now execute the real walk and the real logging in their tests. Nothing should
> break; if `test_prompt_streaming.py`'s captured output changes, stop and escalate rather than
> patching around it — that would invalidate the decision to wire the report into the resolver.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md), `run_mypy_check`,
> `run_lint_imports_check` and `run_tach_check`. Fix everything before finishing. One commit.
