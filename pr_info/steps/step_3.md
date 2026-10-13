# Step 3: Wire the comment fetch into `create_status_file`

See [summary.md](./summary.md) for full context, and [step_2.md](./step_2.md)
for the two pure pieces this step wires together. This is the only step that
performs network I/O.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/workspace.py`:
  - new private function `_fetch_marked_comment`
  - modify existing `create_status_file`
- `tests/workflows/vscodeclaude/test_workspace.py`: extend the existing
  `create_status_file` tests.

No change to `session_launch.py` — both of its call sites
(`prepare_and_launch_session`, `regenerate_session_files`) already pass
everything `create_status_file` needs (`issue_number`, `repo_full_name`,
`folder_path`); the function's signature does not change.

## WHAT

```python
def _fetch_marked_comment(project_dir: Path, issue_number: int) -> str | None:
    """Best-effort fetch of the most recent ❌-marked issue comment.

    Never raises: any failure (network, auth, rate limit, or project_dir not
    being a usable git repo yet) is logged as a warning and treated the same
    as "no marked comment found".
    """
```

Modify `create_status_file` to call it after building `content` from
`STATUS_FILE_TEMPLATE`, and append `STATUS_NOTE_TEMPLATE` when a comment is
found. No change to `create_status_file`'s parameter list or return type
(still `None`).

## HOW

- `_fetch_marked_comment` constructs `IssueManager(project_dir=project_dir)`
  — the same construction pattern already used in `handoff.py` and
  `failure_handling.py` — then calls `.get_comments(issue_number)` and
  passes the result to `_find_marked_comment` from Step 2.
- The whole body of `_fetch_marked_comment` (construction + `get_comments`
  call) is wrapped in one `try/except Exception`, matching the existing
  `# pylint: disable=broad-exception-caught` convention used elsewhere in
  this module (e.g. `setup_git_repo`'s git-validity check) and in
  `failure_handling.py`'s own best-effort GitHub calls.
- Import `IssueManager` from `...mcp_workspace_github` in `workspace.py`
  (already imports `mcp_coder.mcp_workspace_git` — add the sibling
  `mcp_workspace_github` import alongside it).
- In `create_status_file`, call `_fetch_marked_comment(folder_path,
  issue_number)` — `folder_path` is the working folder, already a real git
  clone by the time this function runs at both call sites (confirmed:
  `setup_git_repo` always runs first in `prepare_and_launch_session`;
  `regenerate_session_files` only runs against an existing session folder).

## ALGORITHM

```
content = STATUS_FILE_TEMPLATE.format(...)          # unchanged, existing code
note = _fetch_marked_comment(folder_path, issue_number)
if note is not None:
    content += STATUS_NOTE_TEMPLATE.format(comment_body=note)
write content to status_file                        # unchanged, existing code
```

`_fetch_marked_comment` itself:
```
try:
    comments = IssueManager(project_dir=project_dir).get_comments(issue_number)
    return _find_marked_comment(comments)
except Exception as exc:
    log a warning naming issue_number and exc
    return None
```

## DATA

- `_fetch_marked_comment` returns `str | None` (full comment body, or
  `None` on no-match / any failure).
- `create_status_file` still returns `None`; its on-disk output is
  unchanged except for the new trailing block.

## Tests (write first, then implement)

Extend `tests/workflows/vscodeclaude/test_workspace.py`'s existing
`TestCreateStatusFile`-equivalent tests (`test_create_status_file`,
`test_create_status_file_intervention`) are left as-is — they pass
`tmp_path` directly, which is not a git repository, so
`IssueManager(project_dir=...)` raises inside the new `try/except` and the
behavior is identical to today (no block appended). Confirm this by running
them unmodified after the change; do not edit them unless they fail.

Add new tests, monkeypatching
`mcp_coder.workflows.vscodeclaude.workspace.IssueManager`:

- **Found:** mock `.get_comments` to return 3 comments, the most recent
  marked → status file contains `"❌ Last automated note:"` and the marked
  comment's full body.
- **Not found:** mock `.get_comments` to return 3 unmarked comments →
  status file byte-identical to the no-note case (no new block).
- **Fetch raises:** mock `IssueManager(...)` construction (or
  `.get_comments`) to raise → status file unchanged (no new block), and
  assert a warning was logged (via `caplog`).
- **Fewer than 3 comments exist:** mock `.get_comments` to return a single
  marked comment → still found (confirms the window logic composes
  correctly end-to-end with Step 2's helper, not just in isolation).

## Commit

One commit: the new/extended tests + the two production changes,
`run_pytest_check` / `run_pylint_check` / `run_mypy_check` all passing.

## LLM prompt for this step

> Implement Step 3 of `pr_info/steps/summary.md` (see that file for full
> context), building on Step 2's `_find_marked_comment` and
> `STATUS_NOTE_TEMPLATE`, exactly as specified in `pr_info/steps/step_3.md`:
> add `_fetch_marked_comment` to
> `src/mcp_coder/workflows/vscodeclaude/workspace.py` and wire it into
> `create_status_file`. Write the listed new tests first in
> `tests/workflows/vscodeclaude/test_workspace.py`, confirm they fail, then
> implement until green, and confirm the two pre-existing
> `create_status_file` tests still pass unmodified. Do not change
> `create_status_file`'s signature or `session_launch.py`. Run pytest,
> pylint and mypy; all must pass. Produce exactly one commit for this step.
> If `folder_path` turns out not to reliably be a valid git clone by the
> time `create_status_file` runs at either call site in `session_launch.py`,
> write one line to `pr_info/.blocked.txt` and stop.
