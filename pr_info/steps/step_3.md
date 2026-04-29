# Step 3 — Wire `ensure_truststore()` into `cli/main.main()`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement Step 3
> exactly as specified. Use TDD: write the test in `tests/cli/test_main.py`
> first, see it fail, then add the inline call in `cli/main.py`. Run pylint,
> pytest (fast unit pattern), mypy, and lint-imports. All must pass. This is
> one commit.

## WHERE

- Modified: `src/mcp_coder/cli/main.py`
- Modified: `tests/cli/test_main.py`

## WHAT

### `cli/main.py` change

Add an inline import + call inside `main()`, **after** `setup_logging(log_level)`
and **before** the `try:` block. **Not at module level.**

```python
def main() -> int:
    ...
    setup_logging(log_level)

    from ..utils.ssl_setup import ensure_truststore  # noqa: PLC0415
    ensure_truststore()

    try:
        ...
```

Match the existing style — the inline imports inside `_handle_check_command`
and `_handle_gh_tool_command` use no `# noqa` or `# pylint: disable`. Do NOT
add lint suppressions unless lint actually flags the line.

### `tests/cli/test_main.py` test

Add one positive test that asserts `main()` invokes `ensure_truststore()` once
during a normal command dispatch path:

```python
def test_main_calls_ensure_truststore(...) -> None:
    """main() activates truststore once before dispatching the command."""
    with (
        patch("mcp_coder.cli.main.execute_verify", return_value=0),
        patch("mcp_coder.utils.ssl_setup.ensure_truststore") as mock_ts,
        patch("sys.argv", ["mcp-coder", "verify"]),
    ):
        rc = main()
    assert rc == 0
    mock_ts.assert_called_once()
```

Place the test in a new or existing class; pick a class that already groups
main()-invocation tests.

## HOW

- The `from ..utils.ssl_setup import ensure_truststore` line uses the package's
  relative import style (`..utils...`) for consistency with the file's other
  imports.
- The patch target in the test is `mcp_coder.utils.ssl_setup.ensure_truststore`
  (where the function lives), **not** `mcp_coder.cli.main.ensure_truststore`,
  because the import is function-scoped — the name is bound in `ssl_setup`'s
  module, not `cli.main`'s.
- **Do not promote** the import or call to module level. The constraint
  protects the `--version` short-circuit (argparse `_VersionAction` raises
  `SystemExit` during `parse_args()` before `main()`'s body runs) and ensures
  importing `cli.main` is side-effect-free.

## ALGORITHM

```
parse_args
resolve log level from args
setup_logging(level)
ensure_truststore()           # ← new
try:
    dispatch command
except KeyboardInterrupt: ...
except Exception: ...
```

## DATA

No new return values. No new types. The function still returns `int` exit codes
unchanged.

## TDD note

The test should fail before the call is added (`mock_ts.assert_called_once()`
would see zero calls). After adding the inline call, it passes.

## Acceptance for this step

- `main()` calls `ensure_truststore()` between `setup_logging(...)` and `try:`.
- The new test in `tests/cli/test_main.py` passes.
- Importing `mcp_coder.cli.main` (without calling `main()`) does **not** trigger
  the SSL patch — verify by ensuring no module-level reference to
  `ensure_truststore`.
- `pylint`, `pytest` (fast unit pattern), `mypy`, `lint-imports` all green.
