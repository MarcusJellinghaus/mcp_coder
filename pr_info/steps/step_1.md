# Step 1 — `claude_md_paths()` + `is_claude_md` refactor

**Depends on:** the pre-flight marker probe in [summary.md](summary.md#manual-actions-no-commits--schedule-around-the-code-steps).
**Do not start until the probe has confirmed the marker comes back.**

**Goal:** put the knowledge of *where Claude looks for `CLAUDE.md` in one directory* in exactly
one place, so Step 3's finder and the existing `is_claude_md` cannot drift apart.

**No behaviour change.** This step is pure refactor + regression tests.

---

## WHERE

- `src/mcp_coder/prompts/prompt_loader.py` — add `claude_md_paths`, refactor `is_claude_md`
  (currently `:134-166`)
- `tests/prompts/test_prompt_loader.py` — new tests

## WHAT

```python
def claude_md_paths(directory: Path) -> list[Path]:
    """Return the CLAUDE.md candidate paths Claude Code looks for in one directory.

    Not existence-checked — these are candidates, not hits.

    Returns:
        [<directory>/CLAUDE.md, <directory>/.claude/CLAUDE.md]
    """
```

Public (no leading underscore): `cli/utils.py` imports it in Step 3, and a cross-module
private import is a smell worth avoiding for a two-line function.

`is_claude_md` keeps its exact signature: `(project_prompt_path: Path | None, project_dir: str | None) -> bool`.

## HOW

- The module has no `__all__`; nothing to register.
- No new imports (`Path` already imported at `prompt_loader.py:8`).
- Three consumers of `is_claude_md` must keep working unchanged:
  `src/mcp_coder/llm/interface.py:63`, `src/mcp_coder/cli/commands/verify.py:365`, and Step 3's
  finder (which uses `claude_md_paths` directly, not `is_claude_md`).

## ALGORITHM

Inside `is_claude_md`, replace **only** the two hardcoded comparisons at `:153` and `:156`:

```
current = project
while True:
    for candidate in claude_md_paths(current):     # was: two literal `if resolved == ...`
        if resolved == candidate.resolve():
            return True
    parent = current.parent
    if parent == current: break
    current = parent
```

Everything else stays byte-identical: the `None` guards at `:142-143`, the `.resolve()` calls
at `:146-147`, the `try/except OSError: return False` guard at `:163-164`, and the trailing
`return False`.

**Critical:** this is a *membership test over every candidate in the ancestor chain*, with no
filesystem existence check. Do not "improve" it into a finder that returns the first existing
file — that flips two real cases from `True` to `False` (a project prompt pointing at
`<repo>/.claude/CLAUDE.md` while `<repo>/CLAUDE.md` also exists; a project prompt pointing at a
parent's `CLAUDE.md` while `<repo>/CLAUDE.md` exists).

## DATA

- `claude_md_paths` → `list[Path]`, always length 2, order `[root-level, .claude/]`. The order
  is presentational only — it is **not** a precedence rule and nothing may treat it as one.
- `is_claude_md` → `bool`, semantics unchanged.

## TESTS (write first)

In `tests/prompts/test_prompt_loader.py`:

**`claude_md_paths`**
1. Returns exactly `[d/"CLAUDE.md", d/".claude"/"CLAUDE.md"]` for a given directory.
2. Does not touch the filesystem — returns both paths for a directory that does not exist.

**`is_claude_md` regression** (these must pass before *and* after the refactor — write them
against the current implementation first, confirm green, then refactor):

3. `<project>/CLAUDE.md` → `True`
4. `<project>/.claude/CLAUDE.md` → `True`
5. `<parent>/CLAUDE.md` where `project` is a subdirectory → `True`
6. Unrelated path (e.g. `<project>/docs/other.md`) → `False`
7. `project_prompt_path is None` → `False`; `project_dir is None` → `False`
8. Returns `True` for a `CLAUDE.md` path that **does not exist on disk** — pins the
   membership-not-existence semantics that the refactor must not break.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Extract claude_md_paths() from is_claude_md (#1113)

Single source for the two CLAUDE.md candidate locations, shared with the
context-root reporting added in a later step. is_claude_md keeps its
membership semantics and OSError guard unchanged.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially "4. Shared candidate knowledge, not a shared
> walk") and `pr_info/steps/step_1.md`, then implement Step 1.
>
> Add a public `claude_md_paths(directory: Path) -> list[Path]` to
> `src/mcp_coder/prompts/prompt_loader.py` returning
> `[directory / "CLAUDE.md", directory / ".claude" / "CLAUDE.md"]`, and make `is_claude_md`
> (at `prompt_loader.py:134-166`) use it in place of its two hardcoded comparisons at `:153`
> and `:156`.
>
> Follow TDD: write the tests in `tests/prompts/test_prompt_loader.py` listed under TESTS
> first. The `is_claude_md` regression tests (3-8) must pass against the **current**
> implementation before you refactor — run them, confirm green, then refactor and confirm they
> are still green.
>
> This is a pure refactor. `is_claude_md` must keep its `while` loop, its early return per
> candidate, its `try/except OSError` guard and its exact signature. It is a membership test
> with no filesystem existence check — do not turn it into a finder.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md), `run_mypy_check`, plus
> `run_lint_imports_check` and `run_tach_check`. Fix everything before finishing. One commit.
