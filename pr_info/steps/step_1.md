# Step 1 — `_flush_round_log` skips the push when nothing was committed

Read [summary.md](./summary.md) first.

Prerequisite for step 2: once the flush runs at the top of every round, an unconditional push
would fire a redundant no-op `git push` on every round, not only on the rounds where something
was actually pending.

## WHERE

- Source: `src/mcp_coder/workflows/review/handoff.py` — `_flush_round_log`, body at lines
  142-153.
- Test: `tests/workflows/review/test_handoff.py` — the `# --- _flush_round_log ---` section,
  after `test_flush_falsy_commit_warns_and_skips_push`.

## WHAT

No signature change:

```python
def _flush_round_log(project_dir: Path, message: str = "Add review round log") -> None:
```

New test:

```python
def test_flush_no_commit_skips_push(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
```

## HOW

- `commit_all_changes` returns a `CommitResult` `TypedDict`
  (`mcp_workspace.git_operations.core`) with keys `success`, `commit_hash`, `error`,
  `error_category`. When there is nothing to commit it returns
  `{"success": True, "commit_hash": None, ...}` — a truthy success that committed nothing.
- Index the key directly (`result["commit_hash"]`), not `.get(...)`: the `TypedDict` declares
  it, so mypy resolves it as `Optional[str]`.
- The test patches `handoff.commit_all_changes` / `handoff.push_changes` with `monkeypatch`,
  matching the four sibling tests in the same section.
- No import changes in either file.

## ALGORITHM

Inside the existing `try:` block, between the `success` check and the push:

```
result = commit_all_changes(message, project_dir)
if not result["success"]:          # unchanged
    warn; return
if result["commit_hash"] is None:  # NEW
    debug("nothing pending"); return
if not push_changes(project_dir):  # unchanged
    warn
```

Log the new branch at **debug**, not warning — nothing pending is the normal case on a clean
tree, and a per-round warning would be noise. Keep it distinct from the `success: False`
warning above it, which reports a real failure.

## DATA

- Returns `None`; the helper stays best-effort and never raises (the surrounding broad
  `except` is unchanged).
- The existing `success: False` test mock omits the `commit_hash` key entirely; that branch
  returns before the new check, so direct indexing is safe.

## TDD

1. Write `test_flush_no_commit_skips_push`: patch `commit_all_changes` to return
   `{"success": True, "commit_hash": None, "error": None, "error_category": None}` and
   `push_changes` to a `MagicMock`. Assert `push.assert_not_called()` and that **no**
   `logging.WARNING` record was emitted (this distinguishes the new quiet path from the
   existing `success: False` path, which does warn). Confirm it fails.
2. Add the three-line guard. Confirm it passes and the four existing `_flush_round_log` tests
   still pass.

## Verification

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/workflows/review/"])
mcp__mcp-tools-py__run_mypy_check
```

Then the full unit suite, then **one commit** for this step.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 only, test-first. In `src/mcp_coder/workflows/review/handoff.py`, make
> `_flush_round_log` skip its `push_changes` call when `commit_all_changes` reports
> `commit_hash is None` — a successful call that committed nothing — logging that at debug
> level. Add exactly one test to the `_flush_round_log` section of
> `tests/workflows/review/test_handoff.py` asserting the push is skipped and no warning is
> emitted; write it before the source change and watch it fail. Change nothing else: no
> signature change, no edits to the four existing `_flush_round_log` tests, no other files.
> Run `run_format_code`, then pylint / pytest (`-n auto`) / mypy, and produce a single commit.
