# Step 3 — Move the Jenkins integration fixtures to `integration_fixtures.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 3** exactly as described in `pr_info/steps/step_3.md`.
> This is a pure refactor: no behaviour change and no new tests. The existing `test_integration.py` must keep working unchanged.
> Run pylint, the fast pytest set, mypy and ruff (`run_ruff_check`). Also run `run_pytest_check(extra_args=["-n", "auto"], markers=["jenkins_integration"])`; those tests pass or skip. All must pass. Then run the formatter and make one commit.

## WHERE

- `tests/utils/jenkins_operations/integration_fixtures.py` — **new**.
- `tests/utils/jenkins_operations/test_integration.py` — remove the two fixtures and the imports only they used.
- `tests/utils/jenkins_operations/conftest.py` — re-export the fixtures.

## WHAT

- Move `jenkins_test_setup` and `jenkins_client` verbatim, including their docstrings and the skip when credentials or `test_job` are missing. Use `mcp__mcp-tools-py__move_symbol` if it handles pytest fixtures; otherwise move them by hand.
- Module docstring: "Shared Jenkins integration-test fixtures. Imported by the conftests that need them, not by the root conftest, so Jenkins setup stays out of unrelated test directories."

## HOW

Add to `conftest.py`, using the redundant-alias form so ruff F401 does not flag it (`pytest_plugins` is only allowed in the root conftest):

```python
from .integration_fixtures import jenkins_client as jenkins_client
from .integration_fixtures import jenkins_test_setup as jenkins_test_setup
```

`test_integration.py` keeps using the fixtures by parameter name; pytest finds them through the conftest.

## ALGORITHM

None (code move only).

## DATA

Unchanged: `jenkins_test_setup` yields `dict[str, str]` with `server_url`, `username`, `api_token` and `test_job`; `jenkins_client` returns a `JenkinsClient`.
