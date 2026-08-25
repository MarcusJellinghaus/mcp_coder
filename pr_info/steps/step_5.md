# Step 5 — `mcp-coder verify` reports the same

**Depends on:** Step 3 (`find_context_claude_md`).
Independent of Steps 6 and 7.

**Goal:** make the agent's rule source checkable **before** a run, not after.

Requirement 6 of the issue. Note this closes a gap rather than adding a capability: verify
already runs Claude at the project directory at both of its LLM call sites (`verify.py:597`,
and `_run_mcp_edit_smoke_test` at `:182`/`:216`, called at `:571`/`:575` with
`str(project_dir)`). That is precisely why verify could never reproduce #1113 — it always
exercised the correct working directory while the workflows did not.

---

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — the PROMPTS section, `:338-374`
- `tests/cli/commands/test_verify_prompts_context.py` — **new file** (see TESTS)

## WHAT

No new function. Two rows appended to the existing `prompt_lines` list, built with the
`_format_row` helper already imported at `verify.py:42` from `.verify_formatting`.

```python
_format_row(label: str, marker: str, value: str, *, indent: int, label_width: int = _LABEL_WIDTH) -> str
```

## HOW

- Import: add `find_context_claude_md` **and `is_outside_project_dir`** to the existing
  `from ..utils import (...)` block at `verify.py:31-35`. Both come from Step 3. Do **not**
  write a second `is_relative_to` comparison here — the "outside `project_dir`" rule has exactly
  one definition, shared with the run-time report, so the two reports cannot drift.
- Insert after the "Claude mode" row (`:355-362`) and **before** the conditional "Redundancy"
  row (`:363-373`), so the Redundancy warning stays adjacent to the project-prompt rows it
  refers to.
- `project_dir` is already in scope at `:334`.
- Walk from `project_dir` — that is where verify runs Claude.
- `symbols` is already in scope (`STATUS_SYMBOLS`-derived, keys `success` / `failure` /
  `warning`).

## ALGORITHM

```
hits = find_context_claude_md(project_dir)            # no stop_at - production walks to root
prompt_lines.append(_format_row("Claude cwd", symbols["success"], str(project_dir), indent=2))
if not hits:
    prompt_lines.append(_format_row("Project instructions", symbols["success"], "none found", indent=2))
else:
    for i, h in enumerate(hits):
        outside = is_outside_project_dir(h, project_dir)       # shared predicate, Step 3
        label  = "Project instructions" if i == 0 else ""      # continuation rows: empty label
        marker = symbols["warning"] if outside else symbols["success"]
        value  = f"{h} (outside project directory)" if outside else str(h)
        prompt_lines.append(_format_row(label, marker, value, indent=2))
```

Label-less continuation rows pass `label=""`; `_format_row` pads the empty label so the value
column stays aligned (see `verify_formatting.py:57`, `:86`).

### Decisions to preserve

- **Every hit at the nearest level**, same rule as Step 3 — never one picked by precedence.
- **`is_outside_project_dir` is imported, not reimplemented.** It also handles the resolution
  mismatch for free: it resolves both sides, so a hit resolved during the walk still compares
  correctly against `project_dir` (already `.resolve()`d at `verify.py:334`, but that is the
  caller's accident, not a contract to depend on).
- **"none found" uses the success marker, not the warning marker.** A project legitimately may
  have no `CLAUDE.md`; the row states the fact without implying breakage. The warning marker is
  reserved for the one genuinely wrong state: a file outside `project_dir`.
- Keep the label short — `_LABEL_WIDTH` is 22 and longer labels overrun without truncation.
- The label must not claim to be a complete account of Claude's memory chain.

## DATA

Output rows appended to `prompt_lines: list[str]`, printed by the existing
`print("\n".join(prompt_lines))` at `:374`. No return value, no exit-code effect — this is
reporting, not verification, so it must **not** feed `verify_exit_code`.

## TESTS (write first)

**New file: `tests/cli/commands/test_verify_prompts_context.py`.** Not the existing
`test_verify.py` — it is already 727 lines, and six more tests would push it past the repo's
750-line guidance (`mcp-coder check file-size --max-lines 750`, CLAUDE.md). Copy the fixture
setup and the invocation pattern from the PROMPTS test class in `test_verify.py:120`, following
its existing `"=== PROMPTS ==="` (`:154`) and `"Redundancy"` (`:230`) assertions.

1. Output contains a "Claude cwd" row naming `project_dir`.
2. Output contains a "Project instructions" row naming `<project_dir>/CLAUDE.md` when it exists.
3. Both files reported when `<project_dir>/CLAUDE.md` and `<project_dir>/.claude/CLAUDE.md`
   both exist.
4. Output contains "none found" — **patch `mcp_coder.cli.commands.verify.find_context_claude_md`
   to return `[]`**. Do not try to arrange an empty subtree on disk: verify calls the walk
   without a `stop_at` boundary, so it runs to the filesystem root and any `CLAUDE.md` in a real
   ancestor of `tmp_path` would falsify the assertion. The walk itself is covered by Step 3's
   tests 6 and 7, which *do* use `stop_at`; what this test owns is the **rendering** of the
   empty result, so stubbing the data source is the honest boundary.
5. A hit outside `project_dir` renders with the warning marker — create
   `tmp_path/"CLAUDE.md"` with `project_dir = tmp_path/"repo"` (no `CLAUDE.md` of its own). This
   is deterministic without a stub: the walk stops at `tmp_path`, one level up.
6. The existing "Redundancy" row still appears in its established position — regression guard
   on the insertion point.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

`tests/cli/commands/test_verify_alignment.py` checks column alignment across verify sections —
if the new rows disturb it, fix the rows, not the alignment test.

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Report project instructions in the verify PROMPTS section (#1113)

verify now names the Claude working directory and every CLAUDE.md at the
nearest ancestor level that has any, warning when one lies outside
project_dir. Same contract as the run-time report, so the agent's rule
source is checkable before a run rather than after.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially "3. Observability becomes a first-class concern")
> and `pr_info/steps/step_5.md`, then implement Step 5.
>
> Add two kinds of row to the PROMPTS section of `src/mcp_coder/cli/commands/verify.py`
> (`:338-374`): a "Claude cwd" row naming `project_dir`, and "Project instructions" rows built
> from `find_context_claude_md(project_dir)` (added in Step 3 — import it from `..utils`).
> Insert them after the "Claude mode" row at `:355-362` and before the conditional "Redundancy"
> row at `:363-373`. Use the existing `_format_row` helper; pass `label=""` for continuation
> rows so the value column stays aligned.
>
> Use `is_outside_project_dir` from `..utils` (also Step 3) to decide the warning marker. Do
> **not** write a fresh `is_relative_to` comparison — that rule has one definition, shared with
> the run-time report.
>
> Report **every** hit at the nearest ancestor level — never pick one by precedence. Use the
> warning marker only for a file lying outside `project_dir`; "none found" uses the success
> marker, since a project may legitimately have no CLAUDE.md. Keep the label short
> (`_LABEL_WIDTH` is 22) and word it so it does not claim to be a complete account of Claude's
> memory chain. These rows are reporting only — they must not affect the verify exit code.
>
> Follow TDD: write the six tests listed under TESTS first, watch them fail, then implement.
> Put them in a **new** `tests/cli/commands/test_verify_prompts_context.py`, not in
> `test_verify.py` (already 727 lines; six more would cross the repo's 750-line guidance).
> Test 4 patches `find_context_claude_md` to return `[]` rather than relying on an empty disk
> subtree — verify walks to the filesystem root, so a real ancestor's `CLAUDE.md` would
> otherwise falsify it.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md) and `run_mypy_check`; check
> that `tests/cli/commands/test_verify_alignment.py` still passes. Fix everything before
> finishing. One commit.
