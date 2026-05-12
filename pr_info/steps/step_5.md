# Step 5 — Surface zombie sessions in status table (Item #4)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_5.md`) in
> full. Step 3 (orphan-workspace cleanup) is a prerequisite — once orphans
> self-clean, zombie rows are the residual diagnostic case. Follow TDD. One
> commit at the end.

## Goal

Make the status table the single source of truth for "what counts toward
`max_sessions`". A session with a closed issue and a missing folder but a
still-live VSCode process must appear in the table so the user can diagnose
blocked launches without parsing `--log-level INFO` output.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/status.py`
- `tests/workflows/vscodeclaude/test_status_display.py`

## WHAT — function signatures

No new functions. `display_status_table` keeps its signature; the change is
inside the body.

```python
def display_status_table(
    sessions: list[VSCodeClaudeSession],
    eligible_issues: list[tuple[str, IssueData]],
    workspace_base: str,
    active_set: dict[str, bool],
    repo_filter: str | None = None,
    cached_issues_by_repo: dict[str, dict[int, IssueData]] | None = None,
    issues_without_branch: set[tuple[str, int]] | None = None,
) -> None: ...
```

## HOW — integration points

- Replace the unconditional skip near `status.py:336`:

```python
# OLD:
if is_closed and not folder_path.exists():
    continue

# NEW:
is_running = active_set.get(session["folder"], False)
if is_closed and not folder_path.exists() and not is_running:
    continue
```

- When `not folder_path.exists() and is_running` (the zombie state):
  - `git_status = "Missing"`
  - `vscode_status = "Running (zombie)"`
  - `action = "-> Investigate zombie"`
  - keep the existing `(Closed)` prefix on the Status column

Move the `is_running = active_set.get(...)` lookup above the skip so it's
available for the conditional skip *and* the column-rendering logic.

## ALGORITHM

```
is_running = active_set.get(session["folder"], False)
folder_missing = not folder_path.exists()
if is_closed and folder_missing and not is_running:
    continue  # nothing to show
if folder_missing and is_running:
    git_status = "Missing"
    vscode_status = "Running (zombie)"
    action = "-> Investigate zombie"
else:
    # existing per-column rendering
    ...
```

## DATA

- Table grows by one row per zombie. No public-API change.
- Three column literals: `"Missing"`, `"Running (zombie)"`,
  `"-> Investigate zombie"`.

## Tests (write first)

In `tests/workflows/vscodeclaude/test_status_display.py`:

1. **Zombie row appears**: build a session with a closed issue (set
   `cached_issues_by_repo[repo][num]["state"] = "closed"`), missing folder
   (`Path(folder).exists() is False`), and
   `active_set[session["folder"]] = True`. Capture `display_status_table`
   output via `capsys`. Assert the row appears with `Running (zombie)`,
   `Missing`, and `-> Investigate zombie`. **Also assert the `(Closed)`
   issue-state prefix on the Status column is preserved on the zombie row**
   — both facts (issue state + zombie process) are conveyed independently
   per summary.md's "keep both since they convey different facts" rationale.
2. **Non-zombie closed + missing still skipped**: same scenario but
   `active_set[folder] = False` → row does NOT appear (existing behavior
   preserved).
3. **Live session with folder present is unaffected**: `is_running=True`,
   folder present → existing VSCode column (`"Running"`, not zombie qualifier).

## Done when

- All tests pass.
- mypy, pylint clean.
- One commit: tests + implementation.
