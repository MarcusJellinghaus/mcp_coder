# review-plan review log 1

## Round 1 — 2026-10-21
**Findings**:
Still reviewing: checking `validate_target_repo` and how upstream `execute_subprocess` handles `env` and `timed_out`.pr_info/steps/step_4.md:84 — medium — The timeout test mocks `timed_out=True, return_code=1` but leaves `execution_error` unset. The real `execute_subprocess` also sets `execution_error="Process timed out after N seconds"` when it times out. As written, an implementation that checks `execution_error` before `timed_out` would still pass, so the test does not enforce the order the issue requires (`timed_out` → `execution_error` → `return_code`). The mock should set `execution_error` too, and the test should assert the reason is "timed out after 300 s".
pr_info/steps/step_4.md:50 — low — The resolver's `PATH` loop keeps relative entries such as `.` and only drops empty ones. A relative `PATH` entry would then search the current directory, which the issue forbids. Drop entries where `Path(e).is_absolute()` is false, and add a `.`-in-`PATH` case to the "cwd is never searched" test at step_4.md:87.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_4.md:84, update the timeout test mock so it matches the real execute_subprocess: set timed_out=True, return_code=1, and execution_error='Process timed out after 300 seconds'. Assert that the reported reason is 'timed out after 300 s'. With all three fields set, the test enforces the timed_out → execution_error → return_code check order.", "In pr_info/steps/step_4.md:50, change the resolver's PATH loop to skip every entry that is not absolute (drop it when Path(e).is_absolute() is false), not just empty entries. In the 'cwd is never searched' test at step_4.md:87, add a case where PATH contains '.' and assert that the current directory is not searched."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-10-22
**Findings**:
Reviewing plan against the upstream runner; checking how `_run_subprocess` handles `env` and `capture_output`.`pr_info/steps/step_4.md:87` — medium — The "not found" test, and the "venv beats PATH" / "PATH fallback" resolution tests at line 88, don't pin `PATH`. A dev or CI machine usually has the real `mcp-coder`, `mcp-workspace` and `mcp-tools-py` on `PATH` from the tool env. So if a test uses one of those names, "not found" finds the real binary and the test fails or depends on the machine. Fix: every phase and resolver test should call `monkeypatch.setenv("PATH", ...)` with a `tmp_path` dir it controls (empty for "not found"), and fake executables should be named with `exe(name)`.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_4.md:87-88, make every phase and resolver test independent of the host PATH. In each one (the 'not found', 'venv beats PATH' and 'PATH fallback' tests), call monkeypatch.setenv('PATH', ...) with a tmp_path directory the test controls; for the 'not found' case that directory is empty. Name the fake executables with exe(name) so that tool binaries already installed on the machine (mcp-coder, mcp-workspace, mcp-tools-py) cannot change the outcome."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-10-22
**Findings**:
The plan has no critical or high findings; one low inconsistency is listed below.

pr_info/steps/step_4.md:28 — low — The phase docstring is labelled "Phase 7", but the same step changes the module docstring to "six" phase functions, and step 6 lists the new phase as the sixth one in `architecture.md`. The plan should use one numbering.
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
