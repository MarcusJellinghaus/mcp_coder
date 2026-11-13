# Step 1 — Move the shared `client` fixture and `_FULL_CONFIG` into `tests/tools/conftest.py`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> This is a pure test refactor: move the duplicated `client` fixture and `_FULL_CONFIG`
> into `tests/tools/conftest.py`, remove the copies, and update the vulture whitelist
> comment. No production code changes. Run pylint, pytest (fast unit tests, `-n auto`)
> and mypy; all must pass. Produce exactly one commit.

## WHERE

- `tests/tools/conftest.py` (modify)
- `tests/tools/test_jenkins_builds.py` (modify)
- `tests/tools/test_jenkins_download_logs.py` (modify)
- `vulture_whitelist.py` (modify comment only)

## WHAT

### `tests/tools/conftest.py` — final content

Keep the two existing re-exports unchanged and add:

```python
"""Test configuration for tools tests."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.utils.jenkins_operations.integration_fixtures import (
    jenkins_client as jenkins_client,
)
from tests.utils.jenkins_operations.integration_fixtures import (
    jenkins_test_setup as jenkins_test_setup,
)

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

# Bare name, not tools.jenkins_builds: the scripts import this module object,
# so the fixture's patches must target it.
jenkins_builds = importlib.import_module("jenkins_builds")

_FULL_CONFIG: dict[str, str | None] = {
    "server_url": "https://jenkins.example.com",
    "username": "user",
    "api_token": "token",
}


@pytest.fixture(name="client")
def fixture_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch config and JenkinsClient; return the client instance mock."""
    monkeypatch.setattr(jenkins_builds, "get_jenkins_config", lambda: _FULL_CONFIG)
    monkeypatch.setattr(jenkins_builds, "load_config", dict)
    client_cls = MagicMock()
    instance: MagicMock = client_cls.return_value
    instance.get_recent_builds.return_value = []
    monkeypatch.setattr(jenkins_builds, "JenkinsClient", client_cls)
    return instance
```

The fixture body is byte-identical to the current copies — move, don't rewrite.

### `tests/tools/test_jenkins_builds.py` and `tests/tools/test_jenkins_download_logs.py`

- Delete the module-level `_FULL_CONFIG` dict.
- Delete the `@pytest.fixture(name="client")` / `fixture_client` function.
- Add `from tests.tools.conftest import _FULL_CONFIG` (in the first-party import block).
- **Keep** each module's own `_TOOL_DIR` / `sys.path` block and
  `jenkins_builds = importlib.import_module("jenkins_builds")` — the missing-config tests
  still patch `jenkins_builds` directly.
- Remove any import that becomes unused (check `MagicMock`, `pytest` — both are still used
  in each file, so likely nothing to remove).

### `vulture_whitelist.py`

Only the comment above `_.fixture_client` changes:

```python
# tests/tools/conftest.py - fixture registered via @pytest.fixture(name="client")
# and injected by pytest, so vulture sees no call site.
_.fixture_client
```

## HOW

- pytest auto-loads `tests/tools/conftest.py` for every module in `tests/tools/`, so the
  `client` fixture is available without import.
- Importing from a conftest is an existing pattern in this repo
  (e.g. `from tests.icoder.conftest import ...`); `tests/tools/__init__.py` exists.

## ALGORITHM

None (refactor).

## DATA

`_FULL_CONFIG: dict[str, str | None]`; fixture returns the `MagicMock` instance that stands
in for `JenkinsClient(...)`.

## Tests

No new tests. TDD does not apply to a pure move: the existing tests in
`test_jenkins_builds.py` and `test_jenkins_download_logs.py` must pass unchanged
(same count, same names).

## Checks

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with the fast-unit-test marker expression and `-n auto`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_vulture_check` (fixture still whitelisted)
- `mcp__mcp-tools-py__run_format_code` before the commit

## Commit

`test(tools): share Jenkins client fixture via conftest`
