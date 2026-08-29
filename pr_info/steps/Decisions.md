# Plan decisions

Corrections approved by the technical lead after the automated review reached its 5-round limit
(see `pr_info/plan_review_log_1.md`). Issue #1132's own Decisions table is settled and untouched.

| # | Decision | Applied in |
|---|---|---|
| 1 | The mechanical test rules must also cover `prompt_llm` / `prompt_llm_stream` calls that pass **no** directory argument today (~90 of them, several behind `claude_api_integration` / `claude_cli_integration`). Added as rule 3, with a grep instruction spanning marker-excluded files. | `step_4a.md` |
| 2 | Six tests pin the removed `None` semantics and must be **deleted or rewritten**, not renamed by rule 1: `test_execution_dir_none_uses_default` (`test_interface.py:339`), `test_execution_dir_none_defaults_to_cwd` (`:759`), the metadata test (`:1343`), and the three cases in `TestPromptLlmProjectDir` (`:1622`), which move onto `inject_prompts`. Listed above the mechanical rules. | `step_4a.md` |
| 3 | Step 1's WHERE row cited the wrong tests. `TestPromptLLMExecutionDirRouting` (`:302-385`) and `TestPromptLLMExecutionDir` (`:723-773`) patch `ask_claude_code_cli` — Claude tests, left to step 4. The langchain assertions step 1 actually breaks are `test_passes_execution_dir_to_langchain` (`:1142-1160`, delete) and the kwarg dicts at `:1437`, `:1561`, `:1583`. | `step_1.md` |
| 4 | The "no parameter goes unused" rationale for 4a's greenness is false. Seven `execution_dir` parameters do go unused after 4a; 4a passes only because pylint `W0613` is disabled project-wide (`pyproject.toml:207`). `env_setup.py:88` is not among them. | `summary.md`, `step_4a.md` |
| 5 | The command docstrings documenting the removed flag belong to **step 3** — that is where the flag stops existing. | `step_3.md` |
| 6 | `test_none_returns_cwd` (`tests/cli/test_utils.py:224`) and `test_default_does_not_warn` (`:355`) fell in neither half of the `TestResolveExecutionDir` split; both are deleted explicitly. | `step_3.md` |
| 7 | Split `step_4.md` into `step_4a.md` and `step_4b.md`. They were already two commits, and `prepare_task_tracker` creates one tracker row per step file. | new files; `summary.md` |
| 8 | Two small additions: `tests/integration/test_mcp_config_integration.py:122` joins 4b's `argparse.Namespace` sweep; step 3 notes that rebinding `project_dir` in `commit.py` also hands a `.resolve()`d path to `validate_git_repository` and the git operations. | `step_4b.md`, `step_3.md` |

**Explicitly out of scope:** the minor line drift in 4a's direct-caller list (`rebase.py:319`,
`task_tracker_prep.py:78`). Precise line numbers are not worth chasing.
