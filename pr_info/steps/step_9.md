# Step 9 — Text and docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_9.md` only.
> Text-only step: no code changes, no tests. Run pylint, mypy and pytest (fast unit markers,
> `-n auto`) to confirm nothing broke. Make exactly one commit.

## WHERE / WHAT

| File | Change |
|---|---|
| `.claude/CLAUDE.md:47` | Tool-mapping row "Format code (black+isort)" → "Format code (project's configured formatter)" |
| `.claude/skills/commit_push/SKILL.md:20` | black/isort wording → "the project's configured formatter" |
| `.claude/skills/implement_direct/SKILL.md:56` | same |
| `docs/repository-setup/python.md:19-20` | `[tool.black]` / `[tool.isort]` rows: formatter selected via `[tool.mcp-tools-py] formatter` or table detection; remove `pyproject_config.py` from "Read by" |
| `docs/repository-setup/python.md` (same table) | Add rows: `[tool.mcp-tools-py] formatter` (read by mcp-tools-py; `"black"`/`"ruff"`; optional while detection is unambiguous) and `[tool.mcp-coder] format_code` (default `true`, opt-out, covers implement, rebase, review, fix-ci, `check_branch_status --fix`). State that a `pyproject.toml` declaring a formatter is required for mcp_coder's formatting |
| `docs/repository-setup/python.md:28` | Remove the claim that `pyproject_config.py` reads `[tool.black]`/`[tool.isort]` and warns on line-length disagreement |
| `docs/repository-setup/python.md:196` | "runs both isort and black" → "runs the project's configured formatter" |
| `docs/configuration/config.md:23` | `pyproject.toml` row: drop "Formatter settings (`[tool.black]`, `[tool.isort]`)"; add `[tool.mcp-coder] format_code` and `[tool.mcp-coder.implement]` (`check_type_hints`); mention `[tool.mcp-tools-py] formatter` read by mcp-tools-py |
| `docs/repository-setup/claude-code.md:103` | "isort+black" → "formatting" |
| `docs/processes-prompts/development-process.md:511, :527` | Neutral wording ("the project's configured formatter") |

Line numbers are approximate — locate by content with `search_files`.

## HOW

Do **not** touch the out-of-scope list in `summary.md` (CI matrix, CI isort job, `tools/*.bat`
references, CI tool table, dependencies readme).

Also do not edit `src/mcp_coder/workflows/rebase_permissions.py` — it lists the MCP tool name
`mcp__mcp-tools-py__run_format_code`, not a formatter.

## Check

`search_files` for `black` / `isort` in the edited files — remaining hits must be the
`[tool.black]` / `[tool.isort]` table names or the out-of-scope lines.
