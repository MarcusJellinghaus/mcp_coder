# Step 2: Move `_get_configured_repos` to `config.py`, Update `cleanup.py`

## Context
See `pr_info/steps/summary.md` for the full architectural overview.
Step 1 must be complete (`session_launch.py` exists).
This step moves the one helper function that belongs in `config.py` and fixes the one external consumer (`cleanup.py`) that currently imports it from `orchestrator`.

This step is done **before** creating `session_restart.py` (Step 3) so that `session_restart.py` can import `_get_configured_repos` from `.config` directly — no temporary import needed.

---

## WHERE

**Modify:** `src/mcp_coder/workflows/vscodeclaude/config.py`
**Modify:** `src/mcp_coder/workflows/vscodeclaude/cleanup.py`

---

## WHAT

### `config.py` — add `_get_configured_repos`

Function moved verbatim from `orchestrator.py`:

```python
def _get_configured_repos() -> set[str]:
    """Get set of repo full names from config."""
    ...
```

Two imports must be added to `config.py` to support it:
- `load_config` from `...utils.user_config` — NOT currently imported (config.py uses `get_config_values`); must be added
- `from .helpers import get_repo_full_name` — NOT currently imported in config.py; must be added

### `cleanup.py` — update import

```python
# Before:
from .orchestrator import _get_configured_repos

# After:
from .config import _get_configured_repos
```

---

## HOW

**In `config.py`:** Add the function at the bottom of the file (after `sanitize_folder_name`), with the additional imports at the top.

---

## ALGORITHM

```
# Changes in this step
1. In config.py: add `load_config` to the user_config imports
2. In config.py: add `from .helpers import get_repo_full_name`
3. In config.py: paste _get_configured_repos() verbatim at end of file
4. In cleanup.py: change `from .orchestrator import` → `from .config import`
```

---

## DATA

```python
def _get_configured_repos() -> set[str]:
    # Returns set of "owner/repo" strings for all repos in [coordinator.repos.*]
    # Returns empty set if no repos configured
    ...
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Step 1 is complete: session_launch.py exists.

Make these two changes:

1. In `src/mcp_coder/workflows/vscodeclaude/config.py`:
   - Add `load_config` to the import from `...utils.user_config`
   - Add `from .helpers import get_repo_full_name`
   - Paste _get_configured_repos() verbatim from orchestrator.py at the end of the file

2. In `src/mcp_coder/workflows/vscodeclaude/cleanup.py`:
   - Change `from .orchestrator import _get_configured_repos`
     to `from .config import _get_configured_repos`

Do NOT modify any logic. Do NOT touch orchestrator.py yet.

After making changes, run:
- mcp__code-checker__run_pylint_check (categories: error, fatal)
- mcp__code-checker__run_mypy_check
- mcp__code-checker__run_pytest_check (extra_args: ["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration"])

Fix any import errors found, but make no logic changes.
```
