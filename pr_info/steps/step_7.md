# Step 7 — Move system-prompt tests to `tests/llm/test_interface_system_prompts.py`; remove allowlist entry

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_7.md`. This is a pure move with `move_symbol` plus one `.large-files-allowlist` line removal: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (new): `tests/llm/test_interface_system_prompts.py`
- `.large-files-allowlist`

## WHAT
- One `move_symbol` call with `["TestPromptLlmInjectPrompts", "TestBuildClaudeSystemPrompts"]` (source order, 4 + 5 = 9 tests). They cover `inject_prompts` → `load_prompts` and `interface._build_claude_system_prompts`.

## HOW
- Method-local imports of `PromptsConfig` and `_build_claude_system_prompts` stay inside their methods.
- The stacked `@patch(..., return_value=...)` decorators on `test_skips_project_prompt_when_claude_md` arrive verbatim.
- Remove the line `tests/llm/test_interface.py` from `.large-files-allowlist`, matched by path. After this move the base keeps only lines 1–17, 325–492, 742–778 and 1985–2249 (about 487 lines). It is already under 600, so the entry would otherwise be reported as stale.

## ALGORITHM
```
dry_run(move_symbol(test_interface.py, [2 classes], test_interface_system_prompts.py))
move_symbol(... same ..., dry_run=False)
edit .large-files-allowlist: delete line "tests/llm/test_interface.py"
format; ruff (F401) -> fix imports only
pylint; mypy; pytest FAST_UNIT; recount; check_file_size; compact diff; commit
```

## DATA
Expected imports in `test_interface_system_prompts.py`:
- `from pathlib import Path`
- `from unittest.mock import MagicMock, patch`
- `from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream`
- `from tests.llm.test_interface import PROJECT_DIR`

`test_interface.py` imports are unchanged.

| Scope | Expected |
|---|---:|
| `tests/llm/test_interface.py` | 18 |
| `tests/llm/test_interface_system_prompts.py` | 9 |
| `tests/llm/` / `tests/prompts/` / whole suite | 1391 / 46 / 6463 |

`check_file_size` passes: `tests/llm/test_interface.py` is about 487 lines, and no stale allowlist entry is reported.

## Blocked if
Any trigger in summary "Failure handling" applies, or a method-local import or `@patch` decorator changed. In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(llm): move system-prompt tests to test_interface_system_prompts; drop allowlist entry`
