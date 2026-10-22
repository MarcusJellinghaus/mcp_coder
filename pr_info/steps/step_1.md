# Step 1 — Pass `branch_name` to both review `prompt_llm` calls

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`
> exactly. TDD: write the tests first (they must fail), then change
> `reviewer.py`, then run format, pylint, mypy and the fast unit tests until
> all pass. Produce exactly one commit for this step. Do not change any
> function signature.

## Precondition

`src/mcp_coder/workflows/review/reviewer.py` must contain exactly two
`prompt_llm(` calls (one in `_run_reviewer`, one inside the `while True:` loop
of `_get_verdict`). If not, write one line to `pr_info/.blocked.txt` and stop.

## 1. Tests (write first)

### WHERE
- `tests/workflows/review/test_reviewer.py`
- `tests/workflows/review/conftest.py`

### WHAT / HOW

`test_reviewer.py`:

- Module constant: `BRANCH = "1270-test-branch"`.
- In fixture `mock_llm` **and** fixture `mock_supervisor_llm`, add:
  ```python
  monkeypatch.setattr(
      reviewer, "get_branch_name_for_logging", MagicMock(return_value=BRANCH)
  )
  ```
- New parametrized test, placed after the existing `_run_reviewer` tests:
  ```python
  @pytest.mark.parametrize(
      "overrides",
      [{}, {"session_id": "rev-1", "tasks": ["Fix foo.py:1"]}],
      ids=["fresh", "task_resume"],
  )
  def test_reviewer_passes_branch_name(
      mock_llm: MagicMock, overrides: dict[str, Any]
  ) -> None:
      _call(**overrides)
      assert mock_llm.call_args.kwargs["branch_name"] == BRANCH
  ```
- New test in the supervisor section:
  `test_verdict_repair_retry_passes_branch_name_on_every_call(monkeypatch, mock_supervisor_llm)`
  - re-patch the helper locally so the test holds the mock handle:
    `branch_mock = MagicMock(return_value=BRANCH)`;
    `monkeypatch.setattr(reviewer, "get_branch_name_for_logging", branch_mock)`
  - `mock_supervisor_llm.side_effect = [
        {"text": "no verdict here", "session_id": "sup-1"},
        {"text": '```json\n{"decision": "dismiss"}\n```', "session_id": "sup-1"},
    ]`
    (round 1 needs a non-`None` session id, otherwise the repair is skipped)
  - `verdict, _ = _call_get_verdict()`
  - assert `verdict is not None`
  - assert `mock_supervisor_llm.call_count == 2`
  - assert every `c.kwargs["branch_name"] == BRANCH` for `c` in `mock_supervisor_llm.call_args_list`
  - `branch_mock.assert_called_once_with(Path("/p"))` (pins "computed once, before the loop")

`conftest.py` — in fixture `env`, next to the `prepare_llm_environment` patch:
```python
monkeypatch.setattr(
    reviewer, "get_branch_name_for_logging", MagicMock(return_value="1072-review")
)
```
No `mocks.` attribute — no core test asserts on it; it only keeps tests off real git.

Red phase: until section 2 lands, these tests fail. `monkeypatch.setattr`
raises because `reviewer` has no `get_branch_name_for_logging` attribute yet,
and once that exists, the `branch_name` kwarg is still missing.

## 2. Implementation

### WHERE
`src/mcp_coder/workflows/review/reviewer.py`

### HOW
Add the import alongside the other `mcp_coder` imports (isort order):
```python
from mcp_coder.utils.git_utils import get_branch_name_for_logging
```

### WHAT
Signatures unchanged:
- `_run_reviewer(config, project_dir, provider, mcp_config, settings_file, issue_number, base_branch, round_number, max_rounds, session_id, tasks, ci_note=None, pr_note=None) -> LLMResponseDict`
- `_get_verdict(config, project_dir, provider, mcp_config, settings_file, supervisor_sid, report, round_number, max_rounds) -> tuple[Verdict | None, str | None]`

### ALGORITHM
```
_run_reviewer:
    env_vars = prepare_llm_environment(project_dir)
    branch_name = get_branch_name_for_logging(project_dir)
    ... build prompt (unchanged) ...
    return prompt_llm(..., settings_file=settings_file, branch_name=branch_name)

_get_verdict:
    env_vars = prepare_llm_environment(project_dir)
    branch_name = get_branch_name_for_logging(project_dir)   # once, before loop
    ... build header/prompt (unchanged) ...
    while True:
        response = prompt_llm(..., settings_file=settings_file, branch_name=branch_name)
        ... unchanged ...
```

### DATA
`branch_name: str | None` — the current branch, or `None` if it cannot be
determined (`get_branch_name_for_logging` never raises). Return values of both
helpers are unchanged.

## 3. Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with the fast unit-test marker filter and `-n auto`

All must pass; then one commit, e.g.
`fix(review): pass branch_name to prompt_llm for MLflow runs (#1270)`.
