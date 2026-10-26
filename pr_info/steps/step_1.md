# Step 1 — Baseline + move fixtures to `conftest.py`

## LLM prompt
> Read `pr_info/steps/summary.md` (especially "Common rules") and this file, `pr_info/steps/step_1.md`. Implement
> step 1 only: record the baseline, then move the fixtures `icoder_app` and `make_icoder_app` from
> `tests/icoder/test_app_pilot.py` to `tests/icoder/conftest.py` with `move_symbol`. Fix imports only. Run the
> step's checks and make exactly one commit.

## WHERE
- `tests/icoder/test_app_pilot.py` (source)
- `tests/icoder/conftest.py` (destination, existing)

## WHAT
These fixtures move verbatim, including their `@pytest.fixture` decorators:
```python
@pytest.fixture
def icoder_app(fake_llm: FakeLLMService, event_log: EventLog) -> ICoderApp: ...

@pytest.fixture
def make_icoder_app(event_log: EventLog) -> Callable[..., ICoderApp]: ...
```

## HOW
- Do this before any test moves. Rope does not import fixtures, because they are parameter names. Moved tests find
  them through the conftest.
- conftest imports after the step: `from collections.abc import Callable, Generator`;
  `from mcp_coder.icoder.services.llm_service import FakeLLMService, LLMService`; add
  `from mcp_coder.icoder.ui.app import ICoderApp` and `from mcp_coder.llm.types import StreamEvent`.
  The two existing function-local `ICoderApp` imports in `patch_icoder_deps` and `_patch_all_icoder_deps` stay unchanged.
- The existing conftest symbols do not change.

## ALGORITHM
```
baseline: collect file (96), tests/icoder/ (1062), whole suite (6463); run file -n auto (96 passed);
          -m "not textual_integration" on the file -> "No Tests Found"
if the file count != 96, or the baseline run / marker check fails -> write one line to pr_info/.blocked.txt and stop
if tests/icoder/ or whole-suite counts differ from summary numbers -> record the actual numbers and use them in later steps (do not block)
move_symbol(["icoder_app", "make_icoder_app"], dest=conftest.py, dry_run=True) -> gate
move_symbol(... real)
fix imports (F401 in test_app_pilot.py, missing names in conftest.py)
run the step checks
```

## DATA
- Collect counts are unchanged: `test_app_pilot.py` 96, `tests/icoder/` 1062, whole suite 6463.
- No test body in `test_app_pilot.py` changed: no `conftest.` prefix and no import of a fixture name.

## Checks
These are the common step checks, with the pytest run on `tests/icoder/test_app_pilot.py` (96 passed). Also run the fast unit suite
from CLAUDE.md with `-n auto`. The conftest is shared by all of `tests/icoder/`.

## Commit
`test(icoder): move app pilot fixtures to conftest (#1323)`
