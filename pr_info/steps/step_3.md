# Step 3 — `validate_target_repo` validates `post_install_checks`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only.
> TDD: write the tests first. Run pylint, mypy and the fast unit pytest set (see
> CLAUDE.md). All must pass. Run the formatter, then make one commit.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py`: `validate_target_repo` (around line 101)
- `tests/workflows/vscodeclaude/test_validate_target_repo.py`

## WHAT
- Add one line inside the existing `try:` block:
  `get_post_install_checks(folder_path, strict=True)` (the result is unused; only validation matters).
- Extend the import from `...utils.pyproject_config`.

## HOW
- A malformed value raises `ValueError` and lands in the existing `except ValueError`
  warning, which already includes the exception text. No new branch is needed.
- An absent key returns `()` and gives no warning; nothing is added to the `else:` block.

## ALGORITHM
None.

## DATA
None.

## Tests (follow the existing test style in the file)
- malformed `post_install_checks` (e.g. `[["ok"], [1]]`) with valid extras and
  github sections → one warning whose text contains `post_install_checks`
- valid `post_install_checks` → no extra warning (the existing `test_no_warnings` fixture setup plus the key)
- the existing `test_no_warnings` (key absent) still passes unchanged
