# Step 1 — Add `[typecheck]` extra to `pyproject.toml`

> Read `pr_info/steps/summary.md` first for full context. This step is the foundation that Step 3 depends on.

## Goal

Promote `mypy` to a first-class declared dependency by adding a new `[typecheck]` optional-dependency group. Add a small test in `tests/test_pyproject_config.py` to lock the contract in place (TDD).

## WHERE

- **Modify** `pyproject.toml` — add one entry under `[project.optional-dependencies]`.
- **Modify** `tests/test_pyproject_config.py` — add one test function.

## WHAT

### `pyproject.toml`

Add this entry adjacent to the existing `types` extra (around line 40, in the same `[project.optional-dependencies]` block):

```toml
typecheck = ["mypy>=1.13.0", "mcp-coder[types]"]
```

No other entries in this section change. Do **not** add `mypy` to `[dev]` or anywhere else — it stays only in `[typecheck]`. (The existing `[dev]` chain still pulls mypy transitively today; that's exactly the latent bug we're hardening against, not removing.)

### `tests/test_pyproject_config.py`

New test function (TDD — write this first, watch it fail, then add the pyproject entry):

```python
def test_pyproject_typecheck_extra_exists() -> None:
    """Verify [typecheck] optional-dependency group exists with mypy + types stubs."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    typecheck = config["project"]["optional-dependencies"]["typecheck"]

    assert any(entry.startswith("mypy>=1.13") for entry in typecheck), (
        f"typecheck extra must declare mypy>=1.13.0, got: {typecheck}"
    )
    assert "mcp-coder[types]" in typecheck, (
        f"typecheck extra must reference [types] stubs group, got: {typecheck}"
    )
```

## HOW

- Reuse the existing `tomllib` + `Path` imports already at the top of `tests/test_pyproject_config.py`. No new imports.
- Place the new test function below the two existing test functions; same style.

## ALGORITHM

```
1. Open pyproject.toml as binary, parse with tomllib.
2. Look up config["project"]["optional-dependencies"]["typecheck"]  -> list[str]
3. Assert at least one entry starts with "mypy>=1.13" (allows future patch-version bumps).
4. Assert "mcp-coder[types]" is in the list (reuses existing stubs group).
```

## DATA

- `typecheck` value type: `list[str]` with exactly two entries:
  - `"mypy>=1.13.0"`
  - `"mcp-coder[types]"`
- Test returns `None`; raises `AssertionError` on contract violation.

## Verification

First, prove the new extra is well-formed end-to-end by installing it:

```
pip install -e .[typecheck]
```

(or `uv pip install -e .[typecheck]`). Confirm the install completes without errors. This proves the new `[typecheck]` extra is well-formed and the self-referential `mcp-coder[types]` resolves.

Then run **all three** quality checks per CLAUDE.md:

```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```

The new test should pass; existing tests should be unaffected.

## Commit

One commit:
```
Add [typecheck] optional-dependency extra (issue #922)

Promotes mypy from a transitive dep (via textual-dev) to a declared
first-class dep. New extra: mypy>=1.13.0 + mcp-coder[types].
Adds a parser test pinning the contract.
```

## LLM prompt for this step

> Implement Step 1 of `pr_info/steps/summary.md`. Read both `pr_info/steps/summary.md` and `pr_info/steps/step_1.md` for full context.
>
> Add a `typecheck` extra to `pyproject.toml` containing `["mypy>=1.13.0", "mcp-coder[types]"]`, and add a `test_pyproject_typecheck_extra_exists` test to `tests/test_pyproject_config.py` that asserts both entries exist. Follow TDD: write the test first, run pytest to confirm it fails, then add the pyproject entry and confirm it passes.
>
> Use only MCP tools. After editing, run the three required quality checks (pytest, pylint, mypy). Make exactly one commit with the message in step_1.md.
