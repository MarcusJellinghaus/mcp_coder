# Step 6 — Rebase checks return `fix_text`; binding-level Done-when test

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 11
(`_run_all_checks` part) and the binding-level "Done when". Depends on Steps 1–3.

## LLM prompt

> Implement Step 6 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_6.md`: make `_run_all_checks` return the `fix_text` per
> action alongside the keys, update its callers, and add the npm-style
> binding-level test (TDD — tests first). The prompt changes and fix-turn
> grants are Step 7. Run the code-quality checks from CLAUDE.md and make
> exactly one commit.

## WHERE

- `src/mcp_coder/workflows/rebase_checks.py` — `_run_all_checks`.
- `src/mcp_coder/workflows/rebase.py` — `run_rebase_workflow` (the three
  `_run_all_checks` calls: baseline, after-rebase, and the re-check in the fix
  loop). The prompt is not changed yet, so all three calls unpack as
  `keys, _ = ...` (an unused local would fail pylint); Step 7 binds `fix_texts`.
- Tests: the existing rebase workflow/check tests (update for the new return
  type); new `tests/workflows/rebase/test_command_toolkit_binding.py`.

## WHAT

```python
FixTexts = dict[str, str]  # action -> fix_text (joined by blank line)

def _run_all_checks(project_dir: Path, automated: bool = False) -> tuple[set[FailureKey], FixTexts]
```

## ALGORITHM

`_run_all_checks`: as today, plus `fix_texts[action]` = `"\n\n"`-join of
`result.fix_text or result.summary` for results with `findings`.

`run_rebase_workflow` (this step):
```
baseline, _ = _run_all_checks(...)
keys, _ = _run_all_checks(...); regressions = keys - baseline     # after rebase
while regressions and attempt < _MAX_FIX_ATTEMPTS:
    ... fix turn ...
    keys, _ = _run_all_checks(...); regressions = keys - baseline # re-check
```
Step 7 replaces `_` with `fix_texts` at the after-rebase call and the re-check
(today `rebase.py:658`), so `fix_texts` is refreshed on every recomputation of
`regressions`.

## DATA

`_run_all_checks` → `({"check: lint"}, {"check": "lint\n..."})`.

## Tests

`rebase_checks` tests: `fix_texts` holds the joined `fix_text` per action with
findings; `ok` / `skipped` actions have no entry; `fix_text=None` falls back
to `summary`.

Rebase workflow tests: callers unpack the tuple; behaviour (keys, stall guard,
attempt cap) unchanged.

`test_command_toolkit_binding.py` (Done when): temp project with only
`mcp-coder.toml` (`toolkit = "command"`, `format.apply`, `check.quick`,
`check.standard`, `test.standard`), steps run small Python scripts that act
like npm through the `fake_npm` fixture from Step 2 — argv such as
`["fakenpm", "lint"]`: shell-safe, and resolved by `shutil.which` on Windows
(`fakenpm.cmd` via PATHEXT) and POSIX (executable shebang script) because the
fixture prepends `bin/` to `PATH`. `_toolkit_class` patched to `CommandToolkit`,
a mock asserting nothing from `mcp_coder.mcp_tools_py` is called:
- `run_formatters(project)` → `True`;
- `run_binding(load_toolkit(p), p, "implement_final")` runs `check@quick`;
- `_run_all_checks(p)` → keys and fix texts for `check@standard` / `test@standard`
  (one script exits 1 → a key `check: <name>` and a `fix_texts["check"]` entry).
