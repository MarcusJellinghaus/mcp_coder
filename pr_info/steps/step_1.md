# Step 1 — Format `tools/` files before lint fixes

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`). Implement only this
> step: run the formatter on `tools/` and commit the result as a formatting-only commit. Do not make any
> lint fixes yet.

## WHERE

`tools/` — the formatter is expected to change exactly these 8 files (all of them also get lint fixes later):

- `tools/safe_delete_folder.py`
- `tools/test_scroll.py`
- `tools/tach_docs.py`
- `tools/test_profiler_plugin/__init__.py`
- `tools/test_profiler_plugin/generate_report.py`
- `tools/mlflow/analyze_bash_commands.py`
- `tools/mlflow/_source_transcripts.py`
- `tools/mlflow/extract_permission_events.py`

## WHAT / HOW

- `mcp__mcp-tools-py__run_format_code(target_directories=["tools"])` (project formatter = isort + black).
- Locally, isort may report that it cannot read 3 mlflow files (Windows `charmap` encoding). Ignore it — black
  still formats them.
- If `git status` shows any changed file outside the list above, check that it has a ruff finding
  (`run_ruff_check(target_directories=["<file>"], extra_args=["--extend-select", "PLW1510", "--extend-ignore", "DOC201,S607"])`).
  If it has none, restore it, because the issue limits formatting to files the fixes touch.

## ALGORITHM

```
run_format_code(tools)
diff = git status / git diff --stat
for f in diff not in expected list: keep only if ruff reports findings for f
run fast unit tests (tests/tools loads these files by path)
commit "style(tools): format files touched by ruff fixes"
```

## DATA

Whitespace and layout changes only. No behavioural change.

## Checks

- Fast unit tests (`-n auto`, the marker exclusion from CLAUDE.md) pass.
- pylint and mypy are unaffected (they do not cover `tools/`). Still run them per CLAUDE.md.
