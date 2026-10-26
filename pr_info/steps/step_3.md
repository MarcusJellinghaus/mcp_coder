# Step 3 — Move mlflow tests to `tests/llm/test_interface_mlflow.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_3.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_mlflow.py`

## WHAT
- One `move_symbol` call with `["TestMlflowConversationIntegration"]` (6 tests; each patches `mcp_coder.llm.interface.mlflow_conversation`).

## HOW
- Both stacked `@patch` decorators on every test must arrive verbatim. The patch targets point at `mcp_coder.llm.interface`, which did not move, so they stay unchanged.

## ALGORITHM
```
dry_run(move_symbol(test_interface.py, ["TestMlflowConversationIntegration"], test_interface_mlflow.py))
move_symbol(... same ..., dry_run=False)
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; recount; check_file_size; compact diff; commit
```

## DATA
Expected imports in `test_interface_mlflow.py`:
- `from pathlib import Path`
- `from typing import Any`
- `from unittest.mock import MagicMock, patch`
- `import pytest`
- `from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm`
- `from mcp_coder.utils.subprocess_runner import TimeoutExpired`
- `from tests.llm.test_interface import PROJECT_DIR`

`test_interface.py` imports are unchanged (`Any` is still used by `TestPromptLlmStreamToolsParam`; `LLMTimeoutError` and `TimeoutExpired` by the copilot classes).

| Scope | Expected |
|---|---:|
| `tests/llm/test_interface.py` | 60 |
| `tests/llm/test_interface_mlflow.py` | 6 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

## Blocked if
Any trigger in summary "Failure handling" applies. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move mlflow conversation tests to test_interface_mlflow`
