# Step 3: Wire `--push` into execute functions + integration tests

**Ref:** See `pr_info/steps/summary.md` for full context (issue #907).

## WHERE

- `src/mcp_coder/cli/commands/commit.py` — `execute_commit_auto()` and `execute_commit_clipboard()`
- `tests/cli/commands/test_commit.py` — new test class

## WHAT

At the end of both `execute_commit_auto` and `execute_commit_clipboard`, after the successful commit logging, add the push call:

```python
if getattr(args, "push", False):
    push_result = _push_after_commit(project_dir)
    if push_result != 0:
        return push_result
```

Using `getattr` avoids breaking existing tests that build `argparse.Namespace` without `push`.

## HOW

**In `execute_commit_auto`:** Insert before the final `return 0` (after the commit message summary logging, around line 96).

**In `execute_commit_clipboard`:** Insert before the final `return 0` (after the commit hash logging, around line 177).

## ALGORITHM

```
# (end of existing execute function, after successful commit)
if getattr(args, "push", False):
    result = _push_after_commit(project_dir)
    if result != 0: return result
return 0
```

## DATA

- `args.push` — `bool` from parser (step 1)
- `_push_after_commit()` — returns `int` (step 2)

## Tests (write first)

Add `TestCommitAutoPush` and `TestCommitClipboardPush` classes in `tests/cli/commands/test_commit.py`.

### TestCommitAutoPush

1. **`test_commit_auto_push_called_on_success`** — Mock successful commit, set `args.push=True`, patch `_push_after_commit` to return 0. Assert `_push_after_commit` called with `project_dir`. Assert overall return 0.
2. **`test_commit_auto_push_failure_returns_2`** — Mock successful commit, set `args.push=True`, patch `_push_after_commit` to return 2. Assert overall return 2.
3. **`test_commit_auto_no_push_flag`** — Mock successful commit, set `args.push=False`. Assert `_push_after_commit` NOT called. Assert return 0.
4. **`test_commit_auto_push_not_called_on_commit_failure`** — Mock failed commit (returns 2). Set `args.push=True`. Assert `_push_after_commit` NOT called.

### TestCommitClipboardPush

5. **`test_commit_clipboard_push_called_on_success`** — Mock successful clipboard commit, set `args.push=True`, patch `_push_after_commit` to return 0. Assert called, assert return 0.
6. **`test_commit_clipboard_push_failure_returns_2`** — Same but `_push_after_commit` returns 2. Assert return 2.
7. **`test_commit_clipboard_no_push_flag`** — `args.push=False`. Assert `_push_after_commit` NOT called.

## Commit

`feat(cli): integrate --push into commit auto and clipboard`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context, then implement step 3.
> Add the push call to the end of both `execute_commit_auto` and `execute_commit_clipboard` in `src/mcp_coder/cli/commands/commit.py`.
> Use `getattr(args, "push", False)` for backwards compatibility with existing tests.
> Write tests first in `tests/cli/commands/test_commit.py`, patching `_push_after_commit` on the module path.
> Run all code quality checks. Commit with message: `feat(cli): integrate --push into commit auto and clipboard`
