# Step 1: `format_best_effort` helper and the autouse `formatter_mocks` fixture

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest
> set (`-n auto`, the non-integration marker filter from CLAUDE.md). Format,
> then make exactly one commit.

## WHERE

- `src/mcp_coder/workflow_steps/commit.py`: new function `format_best_effort`
- `tests/conftest.py`: new autouse fixture `formatter_mocks`
- `pyproject.toml`: register the `real_formatters` marker
- `tests/workflow_steps/test_commit_format_best_effort.py` (new)
- `tests/test_formatter_mocks_fixture.py` (new)
- The tests that need the real `workflow_steps.ci.run_formatters`
  (`tests/workflow_steps/test_ci_fix_loop.py`, `tests/workflows/fix_ci/test_core.py`,
  `tests/cli/commands/test_check_branch_status_auto_fixes.py`, i.e. the users of
  `tests/ci_fix_drive.py`) get the marker. So does
  `tests/workflows/implement/test_core.py::test_format_code_false_skips_formatter`:
  it patches `commit.run_binding` and asserts it is not called, which would
  pass vacuously with `implement.core.run_formatters` mocked. So does any other
  test that fails because the fixture now replaces a formatter it relied on.
- Rule: any test that patches `commit.run_binding`, `load_toolkit` or
  `get_format_code` but calls through a workflow module needs
  `real_formatters`, or must restore the real function itself, as
  `test_core_formatter_preflight.py` and `rebase/test_workflow_regression.py`
  already do (`monkeypatch.setattr(<module>, "run_formatters", commit.run_formatters)`).

## WHAT

```python
def format_best_effort(project_dir: Path, context: str) -> None:
    """Run the commit binding's formatters; never raise.

    A raised exception or a False result logs a WARNING naming ``context``,
    so the caller's commit always proceeds.
    """
```

```python
@pytest.fixture(autouse=True)
def formatter_mocks(request: pytest.FixtureRequest) -> Generator[SimpleNamespace, None, None]:
    """Replace run_formatters / format_best_effort in every importing mcp_coder module."""
```

## HOW

- Add `format_best_effort` to `commit.py` after `run_formatters`. It calls
  `run_formatters` in the same module.
- The fixture imports `mcp_coder.workflow_steps.commit` lazily, inside the
  fixture body, like `_resolvable_formatter`. It uses `patch.object` inside a
  `contextlib.ExitStack`, not monkeypatch (see `_resolvable_formatter`'s
  docstring for why).
- Tests that need the shared mocks request `formatter_mocks` by name.
- Never patch `mcp_coder.workflow_steps.commit` itself.
- The scan only sees modules already loaded when the fixture runs. Every
  current importer of `run_formatters` (under `workflows/` and
  `workflow_steps/`) is imported at collection time by its own tests. Say so in
  the fixture docstring.
- Existing tests that patch `<module>.run_formatters` explicitly keep working:
  their patch is applied after the fixture's and undone first.
- `pyproject.toml` markers list: add
  `"real_formatters: opt out of the autouse formatter_mocks patch of run_formatters / format_best_effort"`.

## ALGORITHM

```
format_best_effort(project_dir, context):
    try: ok = run_formatters(project_dir)
    except Exception as e: logger.warning("Formatting failed before %s: %s", context, e); return
    if not ok: logger.warning("Formatting failed before %s", context)

formatter_mocks(request):
    mocks = SimpleNamespace(run_formatters=MagicMock(return_value=True), format_best_effort=MagicMock(return_value=None))
    if marker "real_formatters": yield mocks; return
    for mod in list(sys.modules.values()) whose __name__ starts with "mcp_coder." and != commit module:
        for name in ("run_formatters", "format_best_effort"):
            if getattr(mod, name, None) is getattr(commit, name): stack.enter_context(patch.object(mod, name, getattr(mocks, name)))
    yield mocks
```

## DATA

- `format_best_effort` returns `None`.
- `formatter_mocks` yields
  `SimpleNamespace(run_formatters: MagicMock, format_best_effort: MagicMock)`.

## Tests first

`tests/workflow_steps/test_commit_format_best_effort.py` (patch
`mcp_coder.workflow_steps.commit.run_formatters` directly in each test):

- True: no WARNING logged.
- False: one WARNING containing the context.
- `FormatterConfigError` raised: WARNING with the message, no raise.
- `RuntimeError` raised: WARNING, no raise.

`tests/test_formatter_mocks_fixture.py`:

- `mcp_coder.workflows.implement.core.run_formatters is formatter_mocks.run_formatters`.
- `mcp_coder.workflow_steps.ci.run_formatters is formatter_mocks.run_formatters`.
- `mcp_coder.workflow_steps.commit.run_formatters` is still the real function
  (compare its `__module__` and `__name__`; it is not a `MagicMock`).
- With `@pytest.mark.real_formatters`, `implement.core.run_formatters` is not a
  `MagicMock`.

## Checks

The full fast suite must pass. A test that fails only because it relied on
the real formatter outside `commit.py` gets `@pytest.mark.real_formatters`
(module-level `pytestmark` where the whole module needs it).

## Commit

`test: patch run_formatters in every importing module via one autouse fixture`
