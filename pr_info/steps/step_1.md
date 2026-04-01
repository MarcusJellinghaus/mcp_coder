# Step 1: Update test to expect new config name (TDD red)

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. This is Step 1 of issue #684.
>
> Update the existing test in `tests/test_pyproject_config.py` to expect the new
> `install-from-github` config section name instead of `from-github`.
> After editing, run all three code quality checks (pylint, mypy, pytest).
> The test SHOULD FAIL (red) because `pyproject.toml` still uses the old name.
> Commit with message: "test: expect install-from-github config key (#684)"

## WHERE

- `tests/test_pyproject_config.py`

## WHAT

Rename references in the existing test function:

```python
# OLD
def test_pyproject_from_github_config_exists() -> None:
    from_github = config["tool"]["mcp-coder"]["from-github"]
    assert "packages" in from_github
    assert isinstance(from_github["packages"], list)
    assert "packages-no-deps" in from_github
    assert isinstance(from_github["packages-no-deps"], list)

# NEW
def test_pyproject_install_from_github_config_exists() -> None:
    install_from_github = config["tool"]["mcp-coder"]["install-from-github"]
    assert "packages" in install_from_github
    assert isinstance(install_from_github["packages"], list)
    assert "packages-no-deps" in install_from_github
    assert isinstance(install_from_github["packages-no-deps"], list)
```

## HOW

- Direct string replacement in the test file
- No new imports or integration points

## DATA

- No new data structures
- Test reads `pyproject.toml` via `tomllib.load()` and asserts key existence

## Expected Outcome

- pylint: PASS
- mypy: PASS  
- pytest: FAIL on `test_pyproject_install_from_github_config_exists` (KeyError: `install-from-github` not yet in pyproject.toml)
