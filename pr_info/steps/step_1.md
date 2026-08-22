# Step 1 — `BLOCKED_FILE` constant + `read_and_clear_blocked()` helper

Pure addition. Nothing calls the helper yet, so this step cannot change behaviour.

## WHERE

| File | Change |
|------|--------|
| `src/mcp_coder/workflow_steps/constants.py` | add `BLOCKED_FILE` |
| `src/mcp_coder/workflows/implement/constants.py` | re-export `BLOCKED_FILE` |
| `src/mcp_coder/workflows/implement/task_processing.py` | add `BLOCKED_REASON_MAX_CHARS`, `BLOCKED_REASON_FALLBACK`, `read_and_clear_blocked()` |
| `tests/workflows/implement/test_task_processing.py` | new test class |

## WHAT

`src/mcp_coder/workflow_steps/constants.py` — directly beside `COMMIT_MESSAGE_FILE`:

```python
BLOCKED_FILE = f"{PR_INFO_DIR}/.blocked.txt"
```

`src/mcp_coder/workflows/implement/constants.py` — same redundant-alias re-export pattern
the file already uses for mypy:

```python
from mcp_coder.workflow_steps.constants import BLOCKED_FILE as BLOCKED_FILE
```

`src/mcp_coder/workflows/implement/task_processing.py`:

```python
BLOCKED_REASON_MAX_CHARS = 500
BLOCKED_REASON_FALLBACK = "Agent reported being blocked but gave no reason"

def read_and_clear_blocked(project_dir: Path) -> str | None: ...
```

## HOW

- Import `BLOCKED_FILE` in `task_processing.py` from `.constants` (add it to the existing
  `from .constants import (...)` block).
- The function is public (no leading underscore) — Steps 3, 5 and 7 import it from
  `task_processing` into `core.py` and `finalisation.py`. Same package, no import cycle.
- Not added to `implement/__init__.py`'s `__all__`; it is internal to the workflow.

## ALGORITHM

```
path = project_dir / BLOCKED_FILE
if not path.exists(): return None
try:    text = path.read_text(encoding="utf-8").strip()
except OSError: log warning; text = ""
finally: path.unlink(missing_ok=True)          # delete even if the read failed
if not text: return BLOCKED_REASON_FALLBACK    # empty marker still counts as blocked
return text[:MAX] + "..." if len(text) > MAX else text
```

## DATA

Returns `str | None`:

| Marker state | Return |
|---|---|
| absent | `None` |
| non-empty | stripped text, truncated to 500 chars + `"..."` |
| empty / whitespace only | `BLOCKED_REASON_FALLBACK` |

Side effect in every present case: the file is deleted.

## TESTS (write first)

New class `TestReadAndClearBlocked` in `tests/workflows/implement/test_task_processing.py`,
using the `tmp_path` fixture (create `tmp_path / "pr_info"` first):

1. `test_returns_none_when_absent` — no marker, no `pr_info/` dir either → `None`, no raise.
2. `test_returns_text_and_deletes_file` — marker with `"pytest times out"` → returns that
   text; `(tmp_path / BLOCKED_FILE).exists()` is `False`.
3. `test_whitespace_only_returns_fallback` — marker containing `"   \n\t"` → returns
   `BLOCKED_REASON_FALLBACK`, file deleted.
4. `test_long_text_truncated` — 900-char marker → result length is
   `BLOCKED_REASON_MAX_CHARS + 3` and it ends with `"..."`.
5. `test_blocked_file_constant` — `BLOCKED_FILE == "pr_info/.blocked.txt"` and the symbol
   is importable from **both** `workflow_steps.constants` and `workflows.implement.constants`.

## COMMIT

`Add BLOCKED_FILE constant and read_and_clear_blocked helper`

## LLM PROMPT

```
Read pr_info/steps/summary.md (sections 1 and 6, and the Data structures table) and
pr_info/steps/step_1.md, then implement Step 1 only.

This is a pure addition: add the BLOCKED_FILE constant and a single
read_and_clear_blocked() helper. Nothing calls the helper yet — do NOT wire it into
process_single_task, core.py or finalisation.py; those are Steps 3, 5 and 7.

Work test-first: write the TestReadAndClearBlocked class described in the step file,
watch it fail, then implement.

Key points:
- One helper, not two. Cleanup callers in later steps just ignore the return value.
- An empty or whitespace-only marker must return BLOCKED_REASON_FALLBACK, never None —
  None means "no marker", and later steps branch on that distinction.
- The file must be deleted even if reading it raises OSError.

Use MCP tools for all file operations. When done, run all three checks and fix
everything they report:
  mcp__tools-py__run_pylint_check
  mcp__tools-py__run_mypy_check
  mcp__tools-py__run_pytest_check with
    extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and
    not claude_api_integration and not formatter_integration and not github_integration
    and not langchain_integration"]

Then run ./tools/format_all.sh and make exactly one commit.
```
