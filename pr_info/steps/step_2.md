# Step 2 — Ruff config: select `PLW1510`, add `tools/` ignores

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`). Implement only this
> step: edit `pyproject.toml` as described. Do not touch CI, scripts or `tools/` code.

## WHERE

`pyproject.toml` — `[tool.ruff.lint]` `select` and `[tool.ruff.lint.per-file-ignores]` (around lines 331–369).

## WHAT

1. In `select`, add one line after `"S",` (or a similar spot):
   ```toml
   # PLW1510 only: the PL prefix would re-enable pylint's disabled R category (PLR09xx).
   "PLW1510",
   ```
2. In `[tool.ruff.lint.per-file-ignores]`, add the following, in the existing comment-then-entry style:
   ```toml
   # tools/: low-priority helper scripts that may move to an MCP server or be deleted;
   # Returns sections are not required there.
   "tools/**" = ["DOC201"]
   # safe_delete_folder.py calls handle.exe / cmd by name on purpose (resolved via PATH).
   "tools/safe_delete_folder.py" = ["S607"]
   ```

## HOW

TDD-style check:
- Before the edit, `run_ruff_check(target_directories=["src", "tests"], extra_args=["--extend-select", "PLW1510"])` → 0 findings.
- After the edit, `run_ruff_check(target_directories=["src", "tests"])` → still 0 findings.
- `run_ruff_check(target_directories=["tools"], max_issues=0)` → shows `PLW1510` (1) and no `DOC201`/`S607`.

If `src`/`tests` show any `PLW1510` hit, write one line to `pr_info/.blocked.txt` and stop.

## ALGORITHM

```
edit select += "PLW1510"
edit per-file-ignores += tools/** DOC201, safe_delete_folder S607
ruff src tests -> 0
ruff tools -> PLW1510 present, DOC201/S607 absent
commit "chore(ruff): select PLW1510, add tools/ ignores"
```

## DATA

Config only. CI still runs `ruff check src tests`, so this commit is green.
