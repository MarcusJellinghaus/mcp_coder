# Step 3 — User-facing strings and `_resolve_base_branch` docstring

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`). Implement only Step 3, test-first:
> 1. Add the test assertion and confirm that it fails.
> 2. Update the four user-facing strings and the docstring as described below.
>
> Keep lines within the project's line length by splitting string literals with implicit concatenation. Run `mcp__mcp-tools-py__run_format_code`, pylint, mypy and the fast pytest suite (see CLAUDE.md) until all pass, then make one commit: `fix(base-branch): note issue-body trust in Base Branch hints (#1275)`.

## Precondition

Each target string below still exists verbatim. If any is missing, write one line to `pr_info/.blocked.txt` and stop.

## Qualifier

`only honoured when the issue body is trusted — see docs/repository-setup/github.md`

Insert it directly after the clause that names `### Base Branch`, not at the end of the string. Keep `--base-branch` as the alternative where it is already mentioned.

## WHERE / WHAT

### 3a. Test first — `tests/workflows/rebase/test_guards.py` (around lines 126–129)

In the test that asserts `"--base-branch" in error` and `"### Base Branch" in error`, add:

```python
assert "issue body is trusted" in error
```

Run it and confirm that it fails before changing `rebase.py`.

### 3b. `src/mcp_coder/workflows/rebase.py` — `_resolve_base_branch(project_dir: Path, base_branch_arg: str | None) -> tuple[str | None, str | None]`

- **Error message (lines 271–275).** The new text is:
  ```python
  f"Base '{branch}' was detected from {source.value}, not named in the "
  "issue; add '### Base Branch' to the issue (only honoured when the issue "
  "body is trusted — see docs/repository-setup/github.md) or pass "
  "--base-branch"
  ```
- **Docstring (lines 256–260).** Replace "a base named in the issue's ``### Base Branch`` is trusted" with:
  `a base named in the issue's ``### Base Branch`` is accepted as-is — that section is only used when the issue body is trusted, otherwise detection falls back to the PR, merge-base or default heuristics —`
  Then continue the docstring as before with "and a base found by the PR, merge-base or default heuristics is accepted only when it is ``main``/``master``…". Light rewording for flow is fine.

### 3c. `src/mcp_coder/cli/parsers.py` — `--base-branch` help (lines 266–268)

Add the qualifier inside the existing parenthetical, after `### Base Branch`, separated by `; `:

```python
help="Base branch to rebase onto (default: auto-detect; needed only when "
"the detected base is not main/master and not named in the issue's "
"### Base Branch; only honoured when the issue body is trusted — see "
"docs/repository-setup/github.md)",
```

### 3d. `src/mcp_coder/workflows/create_pr/core.py` (around line 343)

```python
"Could not detect base branch for PR creation.\n"
"Tip: Add '### Base Branch' section to your GitHub issue (only honoured "
"when the issue body is trusted — see docs/repository-setup/github.md)."
```

### 3e. `src/mcp_coder/workflows/review/handoff.py` — `_REBASE_HANDOFF["no_base"]` (line 65)

```python
"Add a `### Base Branch` section to the issue (only honoured when the "
"issue body is trusted — see docs/repository-setup/github.md), then re-run",
```

Leave `"base_missing"` (line 70) unchanged.

## HOW

These are string-literal edits only. There are no new imports, functions or signatures. `tests/workflows/rebase/test_workflow.py:193-194` injects its own copy of the error string through a monkeypatch, so it needs no change.

## ALGORITHM

None — `_resolve_base_branch` logic is unchanged:
```
if base_branch_arg: return (arg, None)
detected = detect_base_branch_with_source(project_dir)
if detected is None: return (None, "...pass --base-branch")
if source is ISSUE or branch in {main, master}: return (branch, None)
return (None, <updated message>)
```

## DATA

The return types are unchanged: `tuple[str | None, str | None]`, and `_REBASE_HANDOFF: dict[str, tuple[str, str, str]]`.

## Tests

- `tests/workflows/rebase/test_guards.py`: the new assertion passes, and the existing `--base-branch` and `### Base Branch` assertions still pass.
- Full fast unit suite passes.
