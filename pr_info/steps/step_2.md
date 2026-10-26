# Step 2 — Move the claude path of `prompt_llm` to `tests/llm/test_interface_prompt_llm.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_2.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_prompt_llm.py`

## WHAT
- One `move_symbol` call with `["TestPromptLLMRouting", "TestLLMTimeoutErrorNormalization", "TestPromptLLM"]` (source order, 11 + 2 + 13 = 26 tests).

## HOW
- `PROJECT_DIR` stays in the base. The tool adds `from tests.llm.test_interface import PROJECT_DIR`.
- The comment `# Real integration tests for LLM interface are removed` (3 lines above `TestPromptLLM`) must stay in `test_interface.py`. If it travelled, move `TestPromptLLM` back with `move_symbol`, then follow "Blocked if".

## ALGORITHM
```
dry_run(move_symbol(test_interface.py, [3 classes], test_interface_prompt_llm.py))  # lists only these 2 files
move_symbol(... same ..., dry_run=False)
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; recount; check_file_size; compact diff; commit
```

## DATA
Expected imports (order is the formatter's):
- `test_interface_prompt_llm.py`:
  - `import asyncio`
  - `from unittest.mock import MagicMock, patch`
  - `import pytest`
  - `from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm`
  - `from mcp_coder.utils.subprocess_runner import TimeoutExpired`
  - `from tests.llm.test_interface import PROJECT_DIR`
  - No `Path`.
- `test_interface.py`: `import asyncio` is removed. `Any`, `LLMTimeoutError` and `TimeoutExpired` stay, because they are still used by the classes that move later.

| Scope | Expected |
|---|---:|
| `tests/llm/test_interface.py` | 66 |
| `tests/llm/test_interface_prompt_llm.py` | 26 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

New file is about 565 lines (< 600).

## Blocked if
Any trigger in summary "Failure handling" applies. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move prompt_llm claude-path tests to test_interface_prompt_llm`
