# review-plan review log 1

## Round 1 — 2026-11-13
**Findings**:
Checking the plan's assumptions against the install code (`InstallConfig.from_args`, `install()`).Verifying import-linter contracts and the git shim API the plan relies on.Still verifying plan assumptions — now the toolkit config loader (step 2) and verify section (step 6).Checking whether this repo tracks/ignores `uv.lock` (matters for the CI job switched to `mcp-coder setup` in step 7).Checking the existing install integration fixture that step 5 copies.Checking `prepare_env`'s Python-isolation behaviour, which affects step 3's env overlay.Checking whether the CLI writes log files into the project dir (would trip step 3's changed-files check).pr_info/steps/step_4.md:38 — medium — `Path(args.project_dir or ".").resolve()` does not check that the directory exists. A mistyped `--project-dir` has no `pyproject.toml` and no table, so `load_setup_config` returns no steps and `setup` exits 0 with "nothing to do". Fix: when the path is missing or not a directory, log an error and return 1 (without requiring a git repo), and add a test for it.
pr_info/steps/step_1.md:54 — medium — Nothing says how the POSIX-mode tests behave on a Windows host, where implement runs. There `sys.platform` is natively `win32`, so an extensionless `tools/lint` goes through the PATHEXT rules and is not found, and `os.access(X_OK)` is true for any file, so "non-executable file not found" fails. This also applies to the rewritten `TestResolveExe` (line 50). Fix: monkeypatch `sys.platform="linux"` in the POSIX tests, and mark the X_OK case `skipif(sys.platform == "win32")`.
pr_info/steps/step_6.md:5 — low — The precondition only checks steps 1–2, but the algorithm (line 36) calls `venv_search_path`, which step 3 adds. Add step 3 (`venv_search_path`) to the precondition.
pr_info/steps/step_10.md:25 — low — Item 6 says to repeat the resolution rules "same text as `toolkits.md`", but HOW (line 36) says to link rather than repeat. Use one approach: link to `toolkits.md`.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_4.md (around line 38), add an existence check after resolving the project dir: if `Path(args.project_dir or ".").resolve()` does not exist or is not a directory, log an error and return 1. Do this before any git-repo check and don\'t require a git repo for it. Add a test in which a missing `--project-dir` returns 1 and does not print "nothing to do".', 'In pr_info/steps/step_1.md (around lines 50-54), say how the POSIX-mode tests run on a Windows host. They should monkeypatch `sys.platform` to "linux". The non-executable-file (X_OK) case should get `pytest.mark.skipif(sys.platform == "win32")`. Apply the same rule to the rewritten `TestResolveExe` tests.', 'In pr_info/steps/step_6.md (around line 5), add step 3 to the precondition alongside steps 1-2, because the algorithm calls `venv_search_path`, which step 3 adds.', 'In pr_info/steps/step_10.md, remove the instruction in item 6 (line 25) to repeat the resolution rules as "same text as `toolkits.md`". Link to `toolkits.md` instead, as the HOW section (line 36) says.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-13
**Findings**:
Reviewing plan files against the code; now checking the install module the `python` built-in reuses.Still verifying plan assumptions — now `prepare_env`/`execute_subprocess`, which step 3's env overlay relies on.Checking `validate_target_repo` and the CI job the plan changes, then I'll write up findings.pr_info/steps/step_1.md:57 — medium — The test "backslash path treated as path-like" will pass on a Windows host but fail on Linux CI, because `sys.platform` is monkeypatched to `"win32"` while `Path` stays `PosixPath`. On Linux, `project_dir / "tools\\lint"` is one literal file name, so a fixture at `tools/lint.cmd` is never found. Specify that the test either asserts only that the name is not searched on `PATH` (for example, a same-named `.cmd` in a `PATH` dir is ignored and the result is `None`), or is marked `skipif(sys.platform != "win32")`. Apply the same rule to any Windows-absolute `argv0` case.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_1.md (around line 57), mark the "backslash path treated as path-like" test with `pytest.mark.skipif(sys.platform != "win32")`. That test monkeypatches `sys.platform` to "win32", which breaks on Linux CI because `Path` is still `PosixPath` there. Mark any test that resolves a Windows-absolute `argv0` the same way.'], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-11-13
**Findings**:
Plan files read; now checking the install code the `python` built-in reuses.Verifying the git status helper's return shape that step 3's changed-files check relies on.Checking `prepare_env`, which step 3's env overlay relies on.Checking import-linter rules for step 5's integration tests (GitPython in `tests/install`).NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
