# Step 6 — Move `prompt_llm_stream` tests to `tests/llm/test_interface_stream.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_6.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_stream.py`

## WHAT
- One `move_symbol` call with `["TestPromptLlmStream", "TestPromptLlmStreamToolsParam"]` (source order, 12 + 3 = 15 tests).

## HOW
- Plain class move. After it, `typing.Any` is unused in the base, and the tool (or ruff `F401`) removes it.

## ALGORITHM
```
dry_run(move_symbol(test_interface.py, [2 classes], test_interface_stream.py))
move_symbol(... same ..., dry_run=False)
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; recount; check_file_size; compact diff; commit
```

## DATA
Expected imports:
- `test_interface_stream.py`:
  - `from pathlib import Path`
  - `from typing import Any`
  - `from unittest.mock import MagicMock, patch`
  - `import pytest`
  - `from mcp_coder.llm.interface import prompt_llm_stream`
  - `from tests.llm.test_interface import PROJECT_DIR`
- `test_interface.py`: `from typing import Any` is removed.

| Scope | Expected |
|---|---:|
| `tests/llm/test_interface.py` | 27 |
| `tests/llm/test_interface_stream.py` | 15 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

## Blocked if
Any trigger in summary "Failure handling" applies. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move prompt_llm_stream tests to test_interface_stream`
