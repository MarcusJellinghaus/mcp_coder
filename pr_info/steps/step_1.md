# Step 1 — `require_langchain_history()` in the storage layer

**Goal:** add the single public helper that decides whether a langchain session id has a
history file on disk, and raises a message naming the id and the expected path when it does
not.

**Scope:** storage layer only. No caller changes yet — after this step nothing calls the new
function except its tests, and no existing behaviour changes.

Read [summary.md](./summary.md) first.

---

## WHERE

| File | Action |
| --- | --- |
| `src/mcp_coder/llm/storage/session_storage.py` | Add one public function; add its name to `__all__` |
| `tests/llm/storage/test_session_storage.py` | Add two tests to the existing `TestLangchainSessionStorage` class |

Do **not** touch `src/mcp_coder/llm/storage/__init__.py`: the package `__init__` deliberately
does not re-export `load_langchain_history` / `store_langchain_history`, and the new function
follows the same pattern (imported directly from `.session_storage` by its caller in step 2).

Do **not** rename or move `_langchain_session_path` — it stays private.

## WHAT

Add to `src/mcp_coder/llm/storage/session_storage.py`, directly after
`load_langchain_history` (which currently ends the file):

```python
def require_langchain_history(
    session_id: str,
    base_dir: Optional[str] = None,
) -> None:
    """Raise when *session_id* has no history file on disk.

    Guards an explicitly requested session resume. Without this check a
    missing history file is indistinguishable from an empty conversation:
    load_langchain_history() returns [] either way, so the resume would
    silently answer from a blank conversation.

    Args:
        session_id: Session identifier the caller asked to resume.
        base_dir: Optional custom base directory for session files.
            Production never passes this; tests use it to point at a tmp dir.

    Raises:
        ValueError: If no history file exists for *session_id*. The message
            names the requested id and the expected path, so a resume from a
            copied file elsewhere is not misreported as a non-existent id.
    """
```

Add `"require_langchain_history"` to the module's `__all__` list (currently at line 19-25).

## HOW

- Reuse the existing private `_langchain_session_path(session_id, base_dir)` — do not
  duplicate the path construction.
- `Optional` is already imported from `typing`; `Path` is already imported. No new imports.
- Keep the signature shape identical to `load_langchain_history(session_id, base_dir=None)`.

## ALGORITHM

```
path = _langchain_session_path(session_id, base_dir)
if path.exists():
    return
raise ValueError(
    f"Session {session_id!r} has no langchain history. "
    f"Expected history file: {path}"
)
```

## DATA

- **Returns:** `None` on success.
- **Raises:** `ValueError`. Message shape:
  `Session 'ghost-id' has no langchain history. Expected history file: <abs path>/ghost-id.json`
- Uses `!r` on the id so an empty or whitespace id is still visible in the message.
- No `/clear` hint in the message — the same string surfaces in `mcp-coder prompt`, where
  such a hint would be wrong.

## TESTS (write first)

Add to the existing `TestLangchainSessionStorage` class in
`tests/llm/storage/test_session_storage.py` (see the surrounding tmp-`base_dir` style at
lines 333-376), and add `require_langchain_history` to that file's import at line 14:

1. `test_require_history_raises_when_file_missing` — call
   `require_langchain_history("ghost-id", base_dir=str(tmp_path))` inside
   `pytest.raises(ValueError)`; assert the message contains `"ghost-id"` **and**
   `"ghost-id.json"`. This is the test that exercises `_langchain_session_path` against a
   real filesystem.
2. `test_require_history_passes_when_file_exists` — `store_langchain_history("sid", [],
   base_dir=str(tmp_path))` first, then `require_langchain_history("sid",
   base_dir=str(tmp_path))` returns without raising.

Note that test 2 must store an **empty** message list: an empty history file is a valid
session, and the guard keys on file existence, never on content.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check   (extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`, then implement step 1 only.
>
> Work test-first: add the two tests described under TESTS to the existing
> `TestLangchainSessionStorage` class in `tests/llm/storage/test_session_storage.py`, watch
> them fail, then add `require_langchain_history()` to
> `src/mcp_coder/llm/storage/session_storage.py` exactly as specified under WHAT / ALGORITHM
> and add its name to that module's `__all__`.
>
> Constraints: do not rename or move `_langchain_session_path`; do not touch
> `src/mcp_coder/llm/storage/__init__.py`; do not add any caller of the new function (that is
> step 2); no new imports are needed.
>
> Use MCP tools for all file operations. When done, run `run_pylint_check`,
> `run_pytest_check` (with `-n auto` and the integration-marker exclusions from
> `CLAUDE.md`) and `run_mypy_check`, and fix everything they report. Then make exactly one
> commit for this step.
