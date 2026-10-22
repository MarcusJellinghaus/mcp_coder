# Step 3 — Fix `F` findings (dead code) in `tools/`

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`). Implement only this
> step: fix the ruff `F` findings in `tools/` in their own commit. Do not fix `UP` or other rule families here.

## WHERE

`tools/**/*.py`. Expected findings: `F541` ×7, `F401` ×3, `F841` ×1. Known locations:
- `tools/test_profiler_plugin/__init__.py:~87` — `F841` `outcome = yield` in a hookwrapper
- `tools/test_profiler_plugin/__init__.py` and `tools/tach_docs.py` — `F401`, `F541`
- `tools/safe_delete_folder.py` — `F541`

## WHAT / HOW

1. Test first: `run_ruff_check(target_directories=["tools"], select=["F"], max_issues=5)` → lists the 11 findings.
2. `run_ruff_fix(target_directories=["tools"], select=["F"])` — fixes `F541` and most `F401`.
3. Manually:
   - `F841`: replace `outcome = yield` with a bare `yield`.
   - Any remaining `F401` (ruff treats removals in `__init__.py` as unsafe): delete the unused import by hand.
     Before deleting, use `search_files` to confirm nothing imports that name from the module.
4. Re-run step 1's check → 0 findings.

## ALGORITHM

```
ruff check tools --select F   # expect 11
ruff fix tools --select F
manual: bare yield; leftover F401
ruff check tools --select F   # expect 0
run_format_code(target_directories=["tools"])  # keep black-clean
```

## DATA

The only behavioural change is dead-code removal. The hookwrapper still yields exactly once.

## Checks

Fast unit tests (including `tests/tools/`), pylint and mypy pass. Commit:
`fix(tools): remove dead code flagged by ruff F`.
