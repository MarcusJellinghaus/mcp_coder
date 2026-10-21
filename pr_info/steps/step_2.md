# Step 2 — `InstallConfig.post_install_checks` (strict read in `from_args`)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` only.
> TDD: write the tests first. Run pylint, mypy and the fast unit pytest set (see
> CLAUDE.md). All must pass. Run the formatter, then make one commit.

## WHERE
- `src/mcp_coder/install/_env.py`
- `tests/install/test_install_env.py`: new class `TestPostInstallChecksResolution`

## WHAT
- New dataclass field, added last, with no default: `post_install_checks: tuple[tuple[str, ...], ...]`
- `from_args`: `post_install_checks = get_post_install_checks(local_path, strict=True)`,
  read right after the existing `get_install_extras(local_path, strict=True)` line, and passed to `cls(...)`.
- Extend the import: `from ..utils.pyproject_config import get_install_extras, get_post_install_checks`.
- `from_args` docstring `Raises:`: mention a malformed `post_install_checks` value.

## HOW
- No CLI flag, so `tests/install/conftest.py::namespace` stays unchanged.
- If any code outside `from_args` constructs `InstallConfig(...)` directly (search
  `InstallConfig(` in `src/` and `tests/`), pass the new field there too.

## ALGORITHM
None. This is a single read and assignment.

## DATA
- `InstallConfig.post_install_checks`: `()` when nothing is declared.

## Tests (`tests/install/test_install_env.py`)
- declared checks in `tmp_path/pyproject.toml` → `config.post_install_checks == (("a", "--version"),)`
- no key → `()`
- malformed value (e.g. `post_install_checks = [[]]`) → `pytest.raises(ValueError, match="post_install_checks")`
