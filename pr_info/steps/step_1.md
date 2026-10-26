# Step 1 — Record baseline; move `TestIsClaudeMd` to `tests/prompts/test_prompt_loader.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Rules that apply to every step"), then implement `pr_info/steps/step_1.md`. This is a pure move with `move_symbol`: no code changes besides imports. On any failure listed under "Blocked if", write one line to `pr_info/.blocked.txt` and stop. Finish with all checks green and exactly one commit.

## WHERE
- Source: `tests/llm/test_interface.py`
- Destination (existing): `tests/prompts/test_prompt_loader.py`

## WHAT
- Move the class `TestIsClaudeMd` (6 tests of `mcp_coder.prompts.prompt_loader.is_claude_md`). It changes file, nothing else.

## HOW
- The class uses only `Path` and its six method-local `from mcp_coder.prompts.prompt_loader import is_claude_md` lines. The destination already imports `Path` and `is_claude_md` at module level, so it needs no new import.
- The block may land at the top, below the imports and above `_LOADER_LOGGER` / the autouse fixture. Leave it there. Autouse fixtures apply module-wide, and `_clear_prompt_warning_cache` has no effect on `is_claude_md`.

## ALGORITHM
```
baseline = collect(-qq tests/llm tests/prompts) + collect(-q whole suite)   # expect 98/40, 1397, 40, 6463
assert collect(-m FAST_UNIT, the two files) == baseline counts for them     # 98 + 40 = 138
dry_run(move_symbol(test_interface.py, ["TestIsClaudeMd"], tests/prompts/test_prompt_loader.py))
move_symbol(... same ..., dry_run=False)
format; ruff; pylint; mypy; pytest FAST_UNIT; recount; compact diff; commit
```

## DATA — expected counts after this step
| Scope | Before | After |
|---|---:|---:|
| `tests/llm/test_interface.py` | 98 | 92 |
| `tests/prompts/test_prompt_loader.py` | 40 | 46 |
| `tests/llm/` | 1397 | 1391 |
| `tests/prompts/` | 40 | 46 |
| whole suite | 6463 | 6463 |

If the recorded baseline differs from the "Before" column, apply the same deltas. The six-test move and the unchanged suite total must hold.

## Checks specific to this step
- All six method-local `is_claude_md` imports are still inside their methods.
- `test_prompt_loader.py` diff shows only the added class (suppressed as moved). Its imports are unchanged.
- `test_interface.py` imports: unchanged (every import is still used by remaining classes).

## Blocked if
Any trigger in summary "Failure handling" applies, or the baseline marker check is not 138 = 98 + 40 (some test carries an integration marker). In that case write one line to `pr_info/.blocked.txt` and stop.

## Commit
`test(prompts): move TestIsClaudeMd to test_prompt_loader`
