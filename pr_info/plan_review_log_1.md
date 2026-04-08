# Plan Review Log 1 — Issue #724
Started: 2026-04-08

## Round 1 — 2026-04-08

### Findings (18 items from round 1 review)
- `_get_bin_dir` helper duplicated across `llm/env.py`, `utils/mcp_verification.py`, and `icoder/env_setup.py`.
- `prepare_llm_environment()` docstring didn't document the new `MCP_CODER_VENV_PATH` key.
- `verify_mcp_servers` silently swallowed `subprocess.run` failures (non-zero exit, OSError).
- Missing test case for `--version` returning non-zero exit code.
- Step 2 commit message claimed "parametrize over sys.platform" but tests were written as separate win/posix pairs.
- `setup_icoder_environment()` mutated `os.environ`, creating hidden global state and test-isolation hazards under pytest-xdist `-n auto`.
- Considered prepending `MCP_CODER_VENV_PATH` to `PATH` (matching `icoder.bat`) — unnecessary given `.mcp.json` absolute paths.
- `RuntimeInfo.env_vars` semantics unclear: "applied vars" vs "effective final values" vs "computed values".
- Step 3 test list mutated `os.environ` directly instead of using `monkeypatch`.
- Missing test: `env_vars` always contains all three `MCP_CODER_*` keys.
- Missing test: `setup_icoder_environment` does NOT mutate `os.environ`.
- Step 3 didn't acknowledge the intentional behavior change vs `prepare_llm_environment()` venv precedence.
- Step 4 didn't mention or test TUI startup info rendering from `on_mount()`.
- Step 4 had no test for env-setup failure path returning exit code 1.
- Step 4 error handling only listed `FileNotFoundError` — missed `RuntimeError` and `PackageNotFoundError`.
- Unclear whether new symbols should be exported from `__init__.py`.
- Step 1 used local `_get_bin_dir` instead of reusing the Step 2 helper.
- Step 3 imported `_get_bin_dir` (private) from `utils.mcp_verification` — should be public `get_bin_dir`.

### Decisions
All 18 findings accepted. User design decisions:
- **os.environ mutation**: REJECTED — `setup_icoder_environment()` is a pure function; env vars flow via `runtime_info.env_vars` → `RealLLMService` → `subprocess_runner.prepare_env()`.
- **PATH prepend**: SKIPPED — intentional deviation from `icoder.bat`; `.mcp.json` uses absolute `${MCP_CODER_VENV_PATH}\...` paths.
- **Single `get_bin_dir` helper**: defined once (public) in `utils/mcp_verification.py`, imported by `llm/env.py` and `icoder/env_setup.py`.
- **Internal-only exports**: new symbols imported directly from modules; no `__init__.py` additions unless tests require it.
- **Parametrized tests**: preferred single `@pytest.mark.parametrize` over win/posix test pairs.

### Changes
Files edited:
- `pr_info/steps/step_1.md` — swap local `_get_bin_dir` for imported `get_bin_dir`; add docstring update sub-bullet; note Step 2 dependency; forbid `__init__.py` export.
- `pr_info/steps/step_2.md` — promote `get_bin_dir` to public; add `RuntimeError` handling for `subprocess.run` failure/non-zero exit; add two new test cases (nonzero, OSError); collapse win/posix test pairs into parametrized tests; clarify export policy.
- `pr_info/steps/step_3.md` — mark as pure function (no `os.environ` mutation); add PATH-prepend deviation note; clarify `RuntimeInfo.env_vars` semantics ("effective final values"); import public `get_bin_dir`; add test-isolation note (`monkeypatch.setenv`); add `test_env_vars_always_contain_all_three_keys` and `test_does_not_mutate_os_environ`; document intentional venv-precedence deviation; forbid `__init__.py` export.
- `pr_info/steps/step_4.md` — expand exception list (`FileNotFoundError`, `RuntimeError`, `PackageNotFoundError`); add `test_execute_icoder_env_setup_failure_returns_1`; add `test_tui_renders_runtime_info_on_mount` (pilot/snapshot); add intentional behavior-change note linking to `summary.md`.

### Status
committed (to be committed by next agent)

## Round 2 — 2026-04-08

### Findings (10 items from round 2 review)
- Step 1 (add `MCP_CODER_VENV_PATH`) imported `get_bin_dir` from Step 2's yet-to-exist module — circular dependency, Step 1 uncommittable on its own.
- Step 2 (new `prepare_llm_environment` behavior) missing `monkeypatch.setenv`/`delenv` test-isolation note for `VIRTUAL_ENV`/`CONDA_PREFIX` (pytest-xdist `-n auto`).
- Step 4 didn't explicitly state that the existing `prepare_llm_environment()` call plus its `try/except RuntimeError` wrapper must be deleted.
- Step 4 missing note on `env_vars=` contract change: previously could be `None`, now always a populated dict; `RealLLMService` unaffected.
- Step 4 had no test asserting `env_vars` from `RuntimeInfo` is wired into `RealLLMService`.
- Step 3 `test_respects_preset_env_vars` only tested one key — per-key loop in the algorithm not fully covered.
- `RuntimeInfo` field types for path fields unspecified — needed `str` (not `Path`) to match `env_vars` and serialize cleanly into `session_start` event data.
- `RuntimeInfo` missing `python_version` / `claude_code_version` fields hinted at in summary `/info` future use.
- Step ordering in `summary.md` needed to match the swap.
- Round 2 changes should be logged in `plan_review_log_1.md` for traceability.

### Decisions
All 10 findings accepted. No user questions needed.

### User decisions
None this round.

### Changes
Files edited:
- `pr_info/steps/step_1.md` — now contains the `utils/mcp_verification.py` content (swapped from Step 2). Added note explaining it lands first because Step 2 imports `get_bin_dir`.
- `pr_info/steps/step_2.md` — now contains the `prepare_llm_environment` + `MCP_CODER_VENV_PATH` content (swapped from Step 1). Added `monkeypatch.setenv`/`delenv` test-isolation note. Updated reference: `get_bin_dir` created in Step 1 (not Step 2).
- `pr_info/steps/step_3.md` — parametrized `test_respects_preset_env_vars` over all three `MCP_CODER_*` keys. Added `python_version`, `claude_code_version` fields to `RuntimeInfo`. Specified all path fields as `str` with a comment explaining the Path → str conversion at the function boundary.
- `pr_info/steps/step_4.md` — explicit deletion of `prepare_llm_environment()` call + `try/except RuntimeError` wrapper at `icoder.py` ~lines 49-54. Added `env_vars` contract change note. Added `test_execute_icoder_passes_env_vars_to_llm_service`. Expanded `test_execute_icoder_env_setup_failure_returns_1` to cover `PackageNotFoundError`. Renumbered snapshot test 6 → 7.
- `pr_info/steps/summary.md` — swapped Step 1 and Step 2 rows in the implementation table; Step 2 row annotated with "imports `get_bin_dir` from Step 1".

### Status
committed (to be committed next)
