# Step 3: Move `_get_configured_repos` to `config.py`, Update `cleanup.py`

## Context
See `pr_info/steps/summary.md` for the full architectural overview.
Steps 1 and 2 must be complete.
This step moves the one helper function that belongs in `config.py` and fixes the one external consumer (`cleanup.py`) that currently imports it from `orchestrator`.

---

## WHERE

**Modify:** `src/mcp_coder/workflows/vscodeclaude/config.py`
**Modify:** `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
**Modify:** `src/mcp_coder/workflows/vscodeclaude/session_restart.py` — update the temporary import from Step 2

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
- `from ...utils.user_config import load_config` — already present in `config.py` via `get_config_values`; check if `load_config` specifically needs adding
- `from .helpers import get_repo_full_name` — new import for `config.py`

### `cleanup.py` — update import

```python
# Before:
from .orchestrator import _get_configured_repos

# After:
from .config import _get_configured_repos
```

### `session_restart.py` — update temporary import from Step 2

```python
# Before (temporary from Step 2):
from .orchestrator import _get_configured_repos

# After:
from .config import _get_configured_repos
```

---

## HOW

**In `config.py`:** Add the function at the bottom of the file (after `sanitize_folder_name`), with any additional imports it needs at the top. The function uses `load_config` and `get_repo_full_name`.

Check `config.py` current imports:
- `load_config` — NOT currently imported (it uses `get_config_values`); must be added
- `get_repo_full_name` from `.helpers` — NOT currently imported; must be added

---

## ALGORITHM

```
# Changes in this step
1. In config.py: add `load_config` to user_config imports
2. In config.py: add `from .helpers import get_repo_full_name`
3. In config.py: paste _get_configured_repos() verbatim at end of file
4. In cleanup.py: change `from .orchestrator import` → `from .config import`
5. In session_restart.py: change `from .orchestrator import` → `from .config import`
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
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.
Steps 1 and 2 are complete.

Make these three changes:

1. In `src/mcp_coder/workflows/vscodeclaude/config.py`:
   - Add `load_config` to the import from `...utils.user_config`
   - Add `from .helpers import get_repo_full_name`
   - Paste _get_configured_repos() verbatim from orchestrator.py at the end of the file

2. In `src/mcp_coder/workflows/vscodeclaude/cleanup.py`:
   - Change `from .orchestrator import _get_configured_repos`
     to `from .config import _get_configured_repos`

3. In `src/mcp_coder/workflows/vscodeclaude/session_restart.py`:
   - Change `from .orchestrator import _get_configured_repos`
     to `from .config import _get_configured_repos`

Do NOT modify any logic. Do NOT touch orchestrator.py yet.

After making changes, run:
- mcp__code-checker__run_pylint_check (categories: error, fatal)
- mcp__code-checker__run_mypy_check
- mcp__code-checker__run_pytest_check (extra_args: ["tests/workflows/vscodeclaude/"])

Fix any import errors found, but make no logic changes.
```
