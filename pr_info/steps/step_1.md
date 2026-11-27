# Step 1 — `jenkins_watch.py`: narrow `job` for mypy, pin the `--inspect` exit code

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`), then implement
> step 1 only. Write the test first, then the code change, then run the checks listed below
> and commit (one commit).

## WHERE

- `tests/tools/test_jenkins_watch.py`: new test at the end of the file, next to
  `test_repo_without_issue_exits_2`
- `tools/jenkins_watch.py`: `main()`, the `if args.inspect is not None:` branch (~line 561)

## WHAT

Test:

```python
def test_inspect_without_job_exits_2(monkeypatch: pytest.MonkeyPatch) -> None:
```

There is no new production function. `main(argv: list[str] | None = None) -> int` keeps
its signature.

## HOW

- The test patches `jenkins_watch.configured_executor_job` with `lambda: None` and
  `jenkins_watch.make_client` with `lambda: None`. Patching `make_client` keeps the test
  hermetic: if the check ran after `make_client()`, `main` would return 3 and the test
  would fail.
- The test calls `jenkins_watch.main(["--inspect", "7"])` inside
  `pytest.raises(SystemExit)` and asserts `exc_info.value.code == 2`.
- The test pins existing behaviour, so it passes before and after the code change.

## ALGORITHM (code change in `main`)

```
job = args.job or configured_executor_job()          # unchanged
if args.inspect is not None and job is None:          # unchanged, stays before make_client()
    parser.error("--inspect needs --job (no single executor job configured)")
client = make_client() ...                            # unchanged
if args.inspect is not None:
    if job is None:                                   # NEW: never fires; narrows job to str for mypy
        parser.error("--inspect needs --job (no single executor job configured)")
    saved = [inspect_log(client, job, number, ...) ...]   # unchanged
```

Do not use `assert` (ruff S101). Do not move the existing check.

## DATA

Exit codes are unchanged: 2 for `--inspect` without a job, 3 when the Jenkins client
can't be made, 0 or 3 after inspecting.

## Checks before commit

1. `run_format_code(target_directories=["src", "tests", "tools"])`
2. `run_ruff_check(target_directories=["src", "tests", "tools"])`: clean
3. `run_mypy_check(target_directories=["src", "tests", "tools"])`: the two
   `tools/jenkins_watch.py:564` findings are gone. Only the 9 findings fixed in step 2 remain
   (`generate_report.py` ×5, `test_scroll.py`, two mlflow `no-any-return`, `tomllib` no-redef).
4. `run_pylint_check()` and `run_mypy_check()` (default scope): clean
5. `run_pytest_check(extra_args=["-n", "auto", "tests/tools/test_jenkins_watch.py"])`: pass,
   then the fast unit-test run from `.claude/CLAUDE.md`

If mypy still reports `tools/jenkins_watch.py:564` after the change, write one line to
`pr_info/.blocked.txt` and stop.

Commit message: `fix(tools): narrow jenkins_watch --inspect job for mypy`
