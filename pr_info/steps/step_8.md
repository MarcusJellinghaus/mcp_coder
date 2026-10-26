# Step 8 — Move copilot tests to `tests/llm/test_interface_copilot.py`; final verification

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_8.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_copilot.py`

## WHAT
- 8a: `move_symbol` with `["TestPromptLlmCopilotRouting", "TestCopilotSystemPromptHandling", "TestCopilotTimeoutHandling"]` (2 + 3 + 1 tests).
- 8b: `move_symbol` with `["TestCopilotProviderValidation"]` (2 tests). Its block may land above the others; leave it there.

## HOW
- Two calls because of the ≤ 3 symbols-per-call limit.
- After 8a, `LLMTimeoutError` and `TimeoutExpired` are unused in the base and must be removed (by the tool or via ruff `F401`).
- No `.large-files-allowlist` change here: the entry was removed in step 7, where the base first drops below 600 lines.

## ALGORITHM
```
dry_run(8a); move(8a); dry_run(8b); move(8b)          # each dry run lists only the 2 files
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; lint_imports; tach; vulture; check_file_size
recount (all 9 files + totals); marker check on all 9 files; search check; compact diff; commit
```

## DATA
Expected imports:
- `test_interface_copilot.py`:
  - `from unittest.mock import MagicMock, patch`
  - `import pytest`
  - `from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm, prompt_llm_stream`
  - `from mcp_coder.utils.subprocess_runner import TimeoutExpired`
  - `from tests.llm.test_interface import PROJECT_DIR`
- `test_interface.py` (final):
  - `from pathlib import Path`
  - `from unittest.mock import MagicMock, patch`
  - `import pytest`
  - `from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream`
  - Module docstring, `PROJECT_DIR` with its comment, and the "integration tests removed" comment are unchanged.

Final counts (unfiltered and with `-m FAST_UNIT`; both must match):

| File | Tests |
|---|---:|
| `tests/llm/test_interface.py` | 10 |
| `tests/llm/test_interface_prompt_llm.py` | 26 |
| `tests/llm/test_interface_mlflow.py` | 6 |
| `tests/llm/test_interface_stream.py` | 15 |
| `tests/llm/test_interface_logs_dir.py` | 6 |
| `tests/llm/test_interface_langchain.py` | 12 |
| `tests/llm/test_interface_system_prompts.py` | 9 |
| `tests/llm/test_interface_copilot.py` | 8 |
| `tests/prompts/test_prompt_loader.py` | 46 |
| sum of the nine files (= 98 + 40 baseline) | 138 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

## Final checks (in addition to the per-step checks)
- `run_lint_imports_check`, `run_tach_check` and `run_vulture_check` pass, with no config change.
- `check_file_size` passes, reports no stale allowlist entry, and shows all nine files under 600 lines.
- `search_files(pattern="test_interface\\w*\\.(?!py\\b)\\w", glob="tests/**/*.py")` finds 0 matches.
- The compact diff against the base branch (`get_base_branch`) shows, besides suppressed moved blocks:
  - the import removals in `test_interface.py` (`asyncio`, `Any`, `TimeoutExpired`, `LLMTimeoutError`)
  - the seven new files' import blocks
  - blank-line hunks
  - the one allowlist line (removed in step 7)

## Blocked if
Any trigger in summary "Failure handling" applies, or a final check fails. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move copilot tests to test_interface_copilot`
