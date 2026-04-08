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
