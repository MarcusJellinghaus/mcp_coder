# Step 2 — Rename `write_lf_text` → `write_repo_text` (pure refactor)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly. This step is a pure rename and must not change behaviour: no function body changes, no new tests. Run `run_format_code`, then pylint, pytest (`-n auto`, unit markers from CLAUDE.md), mypy, ruff, lint-imports, tach and vulture via the MCP tools. All must pass. This step is one commit.

## WHERE

- `src/mcp_coder/utils/text_io.py` (the module keeps its name)
- the call sites, updated by the rename tool:
  - `cli/commands/define_labels_actions.py`
  - `cli/commands/init_file_access.py` (3 calls)
  - `cli/commands/verify.py`
  - `icoder/permissions/loader.py`
  - `workflows/create_plan/prerequisites.py`
  - `workflows/implement/task_tracker_prep.py`
  - `workflows/review/review_log.py`
  - `workflows/vscodeclaude/workspace.py`
- `tests/utils/test_text_io.py`
- string patch targets (by hand):
  - `tests/cli/commands/test_init_file_access.py` `test_rules_file_not_writable_exits_1_but_finishes_run`: `f"{_MODULE}.write_lf_text"` → `f"{_MODULE}.write_repo_text"`
  - `tests/icoder/test_permissions_loader_schema.py` `test_unwritable_schema_does_not_abort_load`: `"mcp_coder.icoder.permissions.loader.write_lf_text"` → `"...loader.write_repo_text"`

## WHAT

`write_repo_text(path: Path, text: str, *, append: bool = False) -> None` has the same signature and body as `write_lf_text`.

## HOW

1. `mcp__mcp-tools-py__rename_symbol(file="src/mcp_coder/utils/text_io.py", symbol_name="write_lf_text", new_name="write_repo_text")`.
2. `rename_symbol` does not rewrite string literals, so fix the two patch targets above by hand.
3. `search_files(pattern="write_lf_text")` over the whole repo must return no hits (src, tests, docs, `vulture_whitelist.py`). Fix any remaining hit.
4. Confirm that the import lines in the 8 source files now read `write_repo_text`.

## ALGORITHM

None.

## DATA

Unchanged.

## Commit message

`refactor(utils): rename write_lf_text to write_repo_text`
