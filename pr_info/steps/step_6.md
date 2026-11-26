# Step 6 — `is_outside_project_dir` delegates to `check_path_within`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md` exactly. TDD: write the policy test first, then change `is_outside_project_dir`. Run `run_format_code`, then pylint, pytest (`-n auto`, unit markers from CLAUDE.md), mypy, ruff, lint-imports, tach and vulture via the MCP tools. All must pass. This step is one commit.

## WHERE

- `src/mcp_coder/cli/utils.py`
- `tests/cli/test_utils_context_root.py`

## WHAT

### Test first — `tests/cli/test_utils_context_root.py`

Add it after `test_is_outside_project_dir`. `patch` is already imported from `unittest.mock`.

```python
@pytest.mark.parametrize(("error", "expected"), [(ValueError, True), (OSError, False)])
def test_is_outside_project_dir_policy(
    self, tmp_path: Path, error: type[Exception], expected: bool
) -> None:
    """A containment failure is outside; an unresolvable path is never warned about."""
    with patch("mcp_coder.cli.utils.check_path_within", side_effect=error("x")):
        assert is_outside_project_dir(tmp_path / "CLAUDE.md", tmp_path) is expected
```

Patch `mcp_coder.cli.utils.check_path_within`, the name the function looks up, not `mcp_coder.utils.fs.check_path_within`. The existing parametrized test (inside / outside / `None`) stays unchanged and must stay green.

### Implementation — `src/mcp_coder/cli/utils.py`

- Import by name, next to the other `..utils` imports: `from ..utils.fs import check_path_within`.
- Function:

```python
def is_outside_project_dir(path: Path, project_dir: str | Path | None) -> bool:
    """Return True when ``path`` does not lie inside ``project_dir``.

    The single definition of "outside" shared by the run-time report and the
    verify report. Always False when project_dir is None - with no anchor there
    is nothing to be outside of. A path that fails the containment check is
    outside; a path that cannot be resolved (OSError) is not.
    """
    if project_dir is None:
        return False
    try:
        check_path_within(path, Path(project_dir))
    except ValueError:
        return True
    except OSError:
        # Do not warn about a path we could not resolve.
        return False
    return False
```

## HOW

- `check_path_within(path: str | Path, root: Path) -> None` raises `ValueError` (`..`, NUL, outside) or `OSError` (unresolvable, symlink loop).
- The callers (`verify.py`, `report_context_root`) stay unchanged.

## ALGORITHM

```
if project_dir is None -> False
check_path_within(path, Path(project_dir))
  ValueError -> True
  OSError    -> False
no error -> False
```

## DATA

Returns `bool`.

## Commit message

`refactor(cli): is_outside_project_dir delegates to fs.check_path_within`
