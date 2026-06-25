# Step 3 — Relocate the two live helpers (errors.py + fold verify), repoint importers

**Goal:** Move the only two genuinely-live symbols out of `claude_code_api.py`
into their permanent homes **before** the module is deleted in Step 4. This step
is purely additive + repointing — `claude_code_api.py` itself is left intact and
working, so the suite stays green. One commit.

TDD: write the new tests for the relocated symbols first (new `test_errors.py`
test + the `TestVerifyClaudeBeforeUse` tests in the existing verification test
file with corrected patch paths), then add the implementation.

## WHERE

Created:
- `src/mcp_coder/llm/providers/claude/errors.py`
- `tests/llm/providers/claude/test_errors.py`

Modified:
- `src/mcp_coder/llm/providers/claude/claude_cli_verification.py`
- `tests/llm/providers/claude/test_claude_cli_verification.py`
- `src/mcp_coder/workflow_utils/commit_operations.py`
- `tests/workflow_utils/test_commit_operations.py`

## WHAT

- **New `errors.py`** — exception only:
  ```python
  """Claude provider error types."""


  class ClaudeAPIError(Exception):
      """Custom exception for Claude errors with user-friendly messages."""
  ```
- **Fold `_verify_claude_before_use` into `claude_cli_verification.py`:**
  - Change imports to:
    ```python
    from .claude_executable_finder import (
        setup_claude_path,
        verify_claude_installation,
    )
    ```
    (the module currently imports only `verify_claude_installation`; **add**
    `setup_claude_path`). Remove `from .claude_code_api import _verify_claude_before_use`.
  - Paste the `_verify_claude_before_use() -> Tuple[bool, Optional[str], Optional[str]]`
    body verbatim from `claude_code_api.py` (it calls `setup_claude_path()` then
    `verify_claude_installation()`). Add `from typing import Optional, Tuple` as
    needed. `verify_claude()` now calls the local `_verify_claude_before_use()`.
- **`commit_operations.py`:** change
  `from ..llm.providers.claude.claude_code_api import ClaudeAPIError`
  → `from ..llm.providers.claude.errors import ClaudeAPIError`. The
  `except ClaudeAPIError` usage is unchanged.
- **`tests/workflow_utils/test_commit_operations.py:10`:** repoint the same
  import to `...claude.errors`.
- **New `tests/llm/providers/claude/test_errors.py`:** minimal coverage for the
  relocated exception:
  ```python
  import pytest
  from mcp_coder.llm.providers.claude.errors import ClaudeAPIError

  def test_claude_api_error_is_exception() -> None:
      assert issubclass(ClaudeAPIError, Exception)

  def test_claude_api_error_raises_with_message() -> None:
      with pytest.raises(ClaudeAPIError, match="boom"):
          raise ClaudeAPIError("boom")
  ```
- **`tests/llm/providers/claude/test_claude_cli_verification.py`:** add a
  `TestVerifyClaudeBeforeUse` class porting the three tests currently in
  `test_claude_code_api_error_handling.py` (`test_successful_verification`,
  `test_failed_verification`, `test_setup_path_exception`). **Update the `@patch`
  targets** to the new home and drop the integration marker (they are fully
  mocked unit tests):
  ```python
  from mcp_coder.llm.providers.claude.claude_cli_verification import (
      _verify_claude_before_use,
  )
  ...
  @patch("mcp_coder.llm.providers.claude.claude_cli_verification.setup_claude_path")
  @patch("mcp_coder.llm.providers.claude.claude_cli_verification.verify_claude_installation")
  ```
  Keep the existing `TestVerifyClaude` class as-is — its patch of
  `claude_cli_verification._verify_claude_before_use` still resolves (the symbol
  is now defined there).

## HOW (integration points)

- **Do not edit or remove anything in `claude_code_api.py` this step.** It keeps
  its own `ClaudeAPIError`, `_verify_claude_before_use`, and SDK functions so the
  module (and its existing tests) still import and run. Deletion happens in
  Step 4. A temporary duplicate definition is intentional and harmless.
- Import-linter: `errors.py` lives under `mcp_coder.llm.providers.claude`, the
  layer `commit_operations` (workflow_utils) already imports from — no contract
  change needed.

## ALGORITHM

`_verify_claude_before_use` (unchanged from original):
```
try: claude_path = setup_claude_path()           # log/none on failure
except Exception: claude_path = None
result = verify_claude_installation()
if result.found and result.works: return True, result.path, None
return False, result.path, result.error_or_detailed_message
```

## DATA

`_verify_claude_before_use` returns `Tuple[bool, Optional[str], Optional[str]]`
(success, claude_path, error_message). `ClaudeAPIError` is a bare `Exception`
subclass. No structural changes.

## VERIFY

Run formatter, then pylint / mypy / pytest (`-n auto` unit subset) / lint-imports
/ vulture. The new `test_errors.py` and the ported `TestVerifyClaudeBeforeUse`
pass; `commit_operations` and the existing `claude_code_api` tests still pass.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement Step 3
> only: create `llm/providers/claude/errors.py` with `ClaudeAPIError`; fold
> `_verify_claude_before_use` into `claude_cli_verification.py` (adding
> `setup_claude_path` to its imports and removing the `claude_code_api` import);
> repoint the `ClaudeAPIError` import in `commit_operations.py` and
> `tests/workflow_utils/test_commit_operations.py`; add `tests/.../test_errors.py`
> and a `TestVerifyClaudeBeforeUse` class (corrected patch paths, no integration
> marker) to `test_claude_cli_verification.py`. **Leave `claude_code_api.py` and
> its tests untouched** — they are deleted in Step 4. Use MCP workspace tools. Run
> isort+black then `run_pylint_check`, `run_mypy_check`, `run_pytest_check`
> (unit subset `-n auto`), `run_lint_imports_check`, `run_vulture_check`. Fix until
> all pass, then one commit.
