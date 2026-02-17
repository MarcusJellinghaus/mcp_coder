# Step 1 — Tests: `_try_delete_empty_directory` retry behaviour

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

You are implementing tests ONLY — do not modify source code yet.

In `tests/utils/test_folder_deletion.py`, inside class `TestHelperFunctions`,
add three new test methods for `_try_delete_empty_directory`:

1. `test_try_delete_empty_directory_retries_rmdir_before_staging` — verifies that
   when rmdir fails, it is retried (called more than once) before _move_to_staging
   is attempted. Mock `Path.rmdir` to always raise PermissionError and mock
   `time.sleep` to be a no-op. Assert rmdir was called 3 times total.

2. `test_try_delete_empty_directory_succeeds_on_second_attempt` — verifies early
   exit when rmdir succeeds on the second attempt. Mock rmdir to raise on the first
   call, succeed on the second. Assert _move_to_staging is never called and result
   is True.

3. `test_try_delete_empty_directory_sleep_called_between_retries` — verifies
   time.sleep(1) is called between retry attempts (i.e. called exactly twice when
   all three rmdir attempts fail and staging is used). Mock Path.rmdir to always
   fail, mock time.sleep, mock _move_to_staging to return True.

All mocks via monkeypatch. No real filesystem locking required.
Follow the existing test style in the file exactly (pytest, monkeypatch, tmp_path).

Also update these two existing tests to patch `time.sleep` (no-op) so that the
retry loop added in Step 2 does not cause them to actually sleep:
- `test_try_delete_empty_directory_locked_moves_to_staging`
- `test_try_delete_empty_directory_all_fail`
```

---

## WHERE

- **File:** `tests/utils/test_folder_deletion.py`
- **Class:** `TestHelperFunctions` (existing)
- **Modified methods:**
  - `test_try_delete_empty_directory_locked_moves_to_staging` — add `time.sleep` patch
  - `test_try_delete_empty_directory_all_fail` — add `time.sleep` patch
- **New methods:** 3 test methods added inside `TestHelperFunctions`

---

## WHAT

```python
def test_try_delete_empty_directory_retries_rmdir_before_staging(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None: ...

def test_try_delete_empty_directory_succeeds_on_second_attempt(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None: ...

def test_try_delete_empty_directory_sleep_called_between_retries(
    self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None: ...
```

---

## HOW

- Import: `_try_delete_empty_directory` is already imported at the top of the test file
- Patch targets:
  - `Path.rmdir` via `monkeypatch.setattr(Path, "rmdir", mock_rmdir)`
  - `time.sleep` via `monkeypatch.setattr("mcp_coder.utils.folder_deletion.time.sleep", mock_sleep)`
  - `mcp_coder.utils.folder_deletion._move_to_staging` via `monkeypatch.setattr(...)`

---

## ALGORITHM

```
# test 1: rmdir called 3 times before staging
mock rmdir → always raises PermissionError, count calls
mock time.sleep → no-op
mock _move_to_staging → return True
call _try_delete_empty_directory(empty_dir, staging_dir)
assert rmdir call count == 3

# test 2: succeeds on second rmdir attempt
mock rmdir → raise on call 1, succeed on call 2
mock _move_to_staging → track if called
call _try_delete_empty_directory(empty_dir, staging_dir)
assert result is True AND _move_to_staging not called

# test 3: sleep called between retries
mock rmdir → always raise (3 times)
mock time.sleep → record calls
mock _move_to_staging → return True
call _try_delete_empty_directory(empty_dir, staging_dir)
assert sleep called exactly 2 times with argument 1
```

---

## DATA

- All tests return `None` (pytest style)
- `_try_delete_empty_directory` returns `bool`
- `time.sleep` mock records call args in a list for assertion
