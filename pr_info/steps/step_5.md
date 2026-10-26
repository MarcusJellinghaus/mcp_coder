# Step 5 — Move langchain routing tests to `tests/llm/test_interface_langchain.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_5.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_langchain.py`

## WHAT
- One `move_symbol` call with `["TestPromptLlmLangchainRouting"]` (12 tests: `prompt_llm` → langchain, env-var provider resolution).

## HOW
- The class imports `prompt_llm` method-locally 12 times and `datetime` method-locally twice, in the `_make_*_response` helpers. All of these stay inside their methods.
- No module-level `prompt_llm` import is added. A method-local import must never be hoisted.

## ALGORITHM
```
dry_run(move_symbol(test_interface.py, ["TestPromptLlmLangchainRouting"], test_interface_langchain.py))
move_symbol(... same ..., dry_run=False)
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; recount; check_file_size; compact diff; commit
```

## DATA
Expected imports in `test_interface_langchain.py`:
- `from unittest.mock import patch`
- `import pytest`
- `from tests.llm.test_interface import PROJECT_DIR`

`test_interface.py` imports are unchanged.

| Scope | Expected |
|---|---:|
| `tests/llm/test_interface.py` | 42 |
| `tests/llm/test_interface_langchain.py` | 12 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

## Blocked if
Any trigger in summary "Failure handling" applies, or a method-local import was hoisted, dropped or rewritten. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move langchain routing tests to test_interface_langchain`
