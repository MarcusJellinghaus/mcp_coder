# Step 4 — Move `logs_dir` derivation tests to `tests/llm/test_interface_logs_dir.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_4.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_logs_dir.py`

## WHAT
- One `move_symbol` call with `["TestPromptLLMLogsDirDerivation", "TestPromptLLMStreamLogsDirDerivation"]` (source order, 3 + 3 = 6 tests). These are the `logs_dir`-from-`env_vars` tests for both public functions.

## HOW
- Plain class move. The tool adds the `PROJECT_DIR` import from the base.

## ALGORITHM
```
dry_run(move_symbol(test_interface.py, [2 classes], test_interface_logs_dir.py))
move_symbol(... same ..., dry_run=False)
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; recount; check_file_size; compact diff; commit
```

## DATA
Expected imports in `test_interface_logs_dir.py`:
- `from pathlib import Path`
- `from unittest.mock import MagicMock, patch`
- `from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream`
- `from tests.llm.test_interface import PROJECT_DIR`

`test_interface.py` imports are unchanged.

| Scope | Expected |
|---|---:|
| `tests/llm/test_interface.py` | 54 |
| `tests/llm/test_interface_logs_dir.py` | 6 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

## Blocked if
Any trigger in summary "Failure handling" applies. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move logs_dir derivation tests to test_interface_logs_dir`
