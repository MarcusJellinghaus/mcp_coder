# Step 4: Register `llm_integration` marker; remove deprecated test; add E2E integration test

## Context
See [summary.md](./summary.md) for full architectural overview.

This step is the final clean-up and end-to-end validation. It has three parts that naturally belong in one commit:
- **A**: Register the `llm_integration` pytest marker in `pyproject.toml`
- **B**: Remove the deprecated `test_real_mlflow_initialization` test
- **C**: Add the `llm_integration` end-to-end test via `execute_verify()`

Part A must precede Part C (marker must be registered before use). Part B is independent but logically belongs here as the final MLflow test clean-up.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement step 4:
  A) Register the llm_integration pytest marker in pyproject.toml
  B) Remove test_real_mlflow_initialization from tests/integration/test_mlflow_integration.py
  C) Add the end-to-end llm_integration test in tests/integration/test_verify_llm_integration.py

For part C, follow TDD: write the test structure first (it will be skipped without real LLM),
then verify the marker is wired correctly and the test body is sound.
Run pytest (unit tests only, excluding llm_integration), pylint, and mypy to confirm all checks pass.
```

---

## WHERE

### Part A — register marker
| Item | Path |
|------|------|
| Modified config | `pyproject.toml` |

### Part B — remove deprecated test
| Item | Path |
|------|------|
| Modified tests | `tests/integration/test_mlflow_integration.py` |

### Part C — add E2E integration test
| Item | Path |
|------|------|
| New test file | `tests/integration/test_verify_llm_integration.py` |

---

## WHAT

### Part A: `pyproject.toml` marker addition

In the `[tool.pytest.ini_options]` `markers` list, add one entry:
```toml
"llm_integration: end-to-end tests with real LLM call, real MLflow logging, real DB check (slow, requires provider credentials)",
```

Place it after `mlflow_integration` and before `langchain_integration` for alphabetical/logical grouping.

### Part B: `test_real_mlflow_initialization` removal

Delete the `test_real_mlflow_initialization` method from `TestMLflowWithRealInstallation` in `tests/integration/test_mlflow_integration.py`.

**Why safe:** `test_sqlite_backend_with_tilde_expansion` in the same class already covers:
- `MLflowLogger` initialization ✓
- Real SQLite backend creation ✓
- Full conversation logging ✓
- DB content verification ✓

The removed test's only unique contribution was using `file:///` URI — which is the deprecated pattern we are removing.

**Do not remove** `test_real_mlflow_available` or `test_sqlite_backend_with_tilde_expansion`.

### Part C: New E2E test file

```
tests/integration/test_verify_llm_integration.py
```

One test class: `TestVerifyEndToEndWithRealLLM`  
One test method: `test_execute_verify_logs_to_mlflow`  
Marker: `@pytest.mark.llm_integration`

---

## HOW

### Test file location

`tests/integration/` is correct because:
- The `.importlinter` `test_module_independence` contract covers `tests.cli`, `tests.llm`, `tests.utils`, `tests.workflows`, `tests.formatters`, `tests.workflow_utils`, `tests.checks` — **not** `tests.integration`
- The test imports from both `mcp_coder.cli.commands.verify` and `mcp_coder.llm.mlflow_db_utils` — placing it in `tests.cli` would violate the spirit of the contract

### Skip condition

The test skips (not fails) when:
1. MLflow is not installed: `pytest.importorskip("mlflow")`
2. The active provider's prerequisite is not met (Claude CLI not found / no LangChain API key)

Use `pytest.importorskip` at the top of the test rather than a try/except — simpler and pytest-idiomatic.

### Test structure

```python
@pytest.mark.llm_integration
class TestVerifyEndToEndWithRealLLM:
    """End-to-end test: execute_verify() → real LLM → real MLflow → real DB check."""
```

---

## ALGORITHM

```
# In test_execute_verify_logs_to_mlflow:
mlflow = pytest.importorskip("mlflow")
create real SQLite DB path in tmp_path
set MLFLOW_TRACKING_URI env var to sqlite:///db_path
set MLFLOW_ENABLED env var (or patch load_mlflow_config)
args = Namespace(check_models=False, mcp_config=None, llm_method=None, project_dir=None)
before_ts = datetime.now(utc)
exit_code = execute_verify(args)
assert exit_code == 0
stats = query_sqlite_tracking(db_path, experiment_name, since=before_ts)
assert stats.test_prompt_logged is True
```

---

## DATA

### Test method signature
```python
def test_execute_verify_logs_to_mlflow(self, tmp_path: Path) -> None:
```

### MLflow config setup in test
The test must configure a real SQLite MLflow backend. Two approaches — use the simpler one:

**Approach: patch `load_mlflow_config`** (avoids env var pollution):
```python
from mcp_coder.config.mlflow_config import MLflowConfig
from mcp_coder.llm.mlflow_logger import _global_logger  # reset before test

db_path = tmp_path / "verify_test.db"
sqlite_uri = f"sqlite:///{db_path}"

with patch("mcp_coder.utils.mlflow_config_loader.load_mlflow_config") as mock_cfg:
    mock_cfg.return_value = MLflowConfig(
        enabled=True,
        tracking_uri=sqlite_uri,
        experiment_name="verify-integration-test",
        artifact_location=str(tmp_path / "artifacts"),
    )
    # Also reset the global MLflow logger so it picks up the new config
    import mcp_coder.llm.mlflow_logger as _ml
    _ml._global_logger = None

    before_ts = datetime.now(timezone.utc)
    exit_code = execute_verify(args)
```

**Note:** `load_mlflow_config` is called in two places — by `verify_mlflow()` and by `MLflowLogger.__init__()`. Both need to see the patched config, which the context manager covers since both calls happen inside the `with` block.

### Assertions
```python
assert exit_code == 0, f"execute_verify returned {exit_code}"

# DB-level assertion: the test prompt run was logged
from mcp_coder.llm.mlflow_db_utils import query_sqlite_tracking
stats = query_sqlite_tracking(
    str(db_path),
    "verify-integration-test",
    since=before_ts,
)
assert stats.test_prompt_logged is True, (
    f"Expected test prompt run in DB after {before_ts}, "
    f"got: run_count={stats.run_count}, last={stats.last_run_time}"
)
```

### MLflow cleanup (Windows file lock prevention)
```python
# After assertions — release file locks before tmp_path cleanup
try:
    import mlflow as _mlflow
    _mlflow.end_run()
    _mlflow.set_tracking_uri("")
except Exception:
    pass
import mcp_coder.llm.mlflow_logger as _ml
_ml._global_logger = None
```
This pattern is already established in `test_sqlite_backend_with_tilde_expansion` — follow the same teardown.

---

## TESTS

### What is tested by the E2E test

| Concern | Verified by |
|---------|------------|
| `execute_verify()` returns exit 0 | `assert exit_code == 0` |
| Real LLM call succeeds | Exit code 0 implies no crash; test prompt failure would show in output |
| MLflow run logged with correct tag | `query_sqlite_tracking()` with `since=before_ts` |
| `test_prompt_logged=True` | Direct DB query assertion |
| `overall_ok=True` (includes `tracking_data` check) | Exit code 0 (MLflow enabled + prompt logged → no failure) |

### CI behaviour

The `llm_integration` marker means this test is **excluded from the default CI fast path**. The standard exclusion pattern in `pyproject.toml` and the CI workflow should be updated to also exclude `llm_integration`:

```
not ... and not llm_integration
```

Check `docs/architecture/architecture.md` Section 8 (Testing Strategy) and `.github/workflows/ci.yml` for the current exclusion pattern string. Add `llm_integration` to it — but only if there is already a marker exclusion list. If the CI runs all tests without marker filtering, no CI change is needed.

### Unit test run (default, no real LLM)

Running `pytest tests/integration/test_verify_llm_integration.py` without the `llm_integration` marker filter will **skip** the test (not fail), because:
- `pytest.importorskip("mlflow")` skips if mlflow not installed
- Even with mlflow installed, the test still needs a real LLM — it will either skip (if Claude CLI not found) or attempt the call

To run the test explicitly:
```
pytest -m llm_integration tests/integration/test_verify_llm_integration.py -v
```
