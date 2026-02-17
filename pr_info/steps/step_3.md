# Step 3 — Tests: empty "No Git" / "Error" folder deletion in `cleanup_stale_sessions`

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.

You are implementing tests ONLY — do not modify source code yet.

In `tests/workflows/vscodeclaude/test_cleanup.py`, inside class `TestCleanup`,
make the following changes:

### Update existing tests (non-empty folders still skip)

1. `test_cleanup_skips_no_git_folder` — add a file inside `no_git_folder` before
   the test runs, so it is non-empty. The expected behaviour (skipped) is unchanged.

2. `test_cleanup_skips_error_folder` — add a file inside `error_folder` before
   the test runs, so it is non-empty. The expected behaviour (skipped) is unchanged.

### Add 4 new test methods

3. `test_cleanup_deletes_empty_no_git_folder` — empty folder with "No Git" status,
   dry_run=False. Mock delete_session_folder to return True. Assert folder path is
   in result["deleted"] and NOT in result["skipped"].

4. `test_cleanup_dry_run_reports_empty_no_git_folder` — empty folder with "No Git"
   status, dry_run=True. Assert result["deleted"] is empty and printed output
   contains "Add --cleanup to delete".

5. `test_cleanup_deletes_empty_error_folder` — same as test 3 but git_status="Error".

6. `test_cleanup_dry_run_reports_empty_error_folder` — same as test 4 but
   git_status="Error".

Use capsys.readouterr() to check printed output in dry_run tests.
Follow the existing test style exactly (pytest, monkeypatch, tmp_path, capsys).
All stale session mocking via monkeypatch on get_stale_sessions.
```

---

## WHERE

- **File:** `tests/workflows/vscodeclaude/test_cleanup.py`
- **Class:** `TestCleanup` (existing)
- **Modified tests:** 2 (add a file to make folder non-empty)
- **New tests:** 4

---

## WHAT

```python
# Modified (add file inside folder before assertions):
def test_cleanup_skips_no_git_folder(...) -> None: ...
def test_cleanup_skips_error_folder(...) -> None: ...

# New:
def test_cleanup_deletes_empty_no_git_folder(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None: ...

def test_cleanup_dry_run_reports_empty_no_git_folder(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None: ...

def test_cleanup_deletes_empty_error_folder(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None: ...

def test_cleanup_dry_run_reports_empty_error_folder(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str]
) -> None: ...
```

---

## HOW

- `get_stale_sessions` patched via `monkeypatch.setattr("mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions", ...)`
- `delete_session_folder` patched via `monkeypatch.setattr("mcp_coder.workflows.vscodeclaude.cleanup.delete_session_folder", lambda s: True)`
- Folders created with `tmp_path / "folder_name"` then `.mkdir()`
- For non-empty: add `(folder / "some_file.txt").write_text("x")` after `.mkdir()`
- For empty: just `.mkdir()`, no files added
- Dry-run output checked with `capsys.readouterr().out`

---

## ALGORITHM

```
# new test: deletes empty No Git/Error folder (dry_run=False)
create empty folder (mkdir, no files)
patch get_stale_sessions → [(session, "No Git")]  # or "Error"
patch delete_session_folder → return True
result = cleanup_stale_sessions(dry_run=False)
assert folder in result["deleted"]
assert folder NOT in result["skipped"]

# new test: dry run reports empty No Git/Error folder
create empty folder
patch get_stale_sessions → [(session, "No Git")]  # or "Error"
result = cleanup_stale_sessions(dry_run=True)
assert result["deleted"] == []
assert "Add --cleanup to delete" in capsys.readouterr().out
```

---

## DATA

- `cleanup_stale_sessions` returns `dict[str, list[str]]` with keys `"deleted"` and `"skipped"`
- Assertions check membership of `str(folder_path)` in the appropriate list
- Dry-run: `result["deleted"]` must be `[]` (nothing actually deleted)
