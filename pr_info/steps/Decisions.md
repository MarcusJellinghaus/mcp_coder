# Decisions

## D1: W4903 — use inline-disable instead of replacing `onerror=` with `onexc=`

`onexc=` was added in Python 3.12. The project's minimum version is Python 3.11, so replacing `onerror=` would break compatibility. Use `# pylint: disable=deprecated-argument` inline instead. W4903 moved from "mechanical fix" to "inline-disable" category.

## D2: Step granularity — one step per warning type per directory

Split the original 5 steps into 14 steps: 8 for src/, 5 for tests/, 1 for config. Each step targets one warning type (or a small tightly-coupled group) in one directory.

## D3: Use `[tool.pylint.main]` instead of `[tool.pylint.MASTER]`

The config step uses `[tool.pylint.main]` for per-file-ignores to match existing pyproject.toml conventions.

## D4: Verify intentional availability-check imports before removing

The following imports must be verified before removal — they may be intentional try/except availability checks:
- `import langchain_mcp_adapters` and `import langgraph` in `agent.py`'s `_check_agent_dependencies`
- `import mlflow` in `mlflow_logger.py`'s `is_mlflow_available()`

If intentional, use `# pylint: disable=unused-import` instead of removing them.

## D5: Append `per-file-ignores` to existing `[tool.pylint.main]` — no duplicate header

Step 14 must append `per-file-ignores` to the existing `[tool.pylint.main]` section in pyproject.toml. TOML does not allow duplicate section headers, so creating a second `[tool.pylint.main]` would cause a parse error.

## D6: `launch_vscode` — pure underscore rename, no default value change

Step 3's rename of `session_working_dir` to `_session_working_dir` in `launch_vscode` must keep the original signature. No `=None` default should be added — it is a pure parameter rename only.
