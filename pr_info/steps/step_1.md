# Step 1: Import contract and one-off check

## LLM prompt

> Read `pr_info/steps/summary.md` and this file, then implement this step. Add the contract, run the one-off check, delete the throwaway module, and write the result to `pr_info/.commit_message.txt`. This step produces exactly one commit. Do not commit yourself.

## WHERE

- Modify: `.importlinter`
- Create, then delete in this step: `src/mcp_coder/_quality_probe.py`
- Write: `pr_info/.commit_message.txt`

## WHAT

No functions. Add this block directly after the `mcp_checker_isolation` contract, before the "Requests Library Isolation" header:

```ini
# -----------------------------------------------------------------------------
# Contract: Quality Tools Isolation
# -----------------------------------------------------------------------------
# Python quality tools run behind the quality-tool boundary and are never
# imported by mcp_coder. _pytest is its own top-level package, so the pytest
# entry doesn't cover it.
# Running them as a subprocess is caught by `tools/check_forbidden_calls.py`
# (rule `quality-tools`).
# -----------------------------------------------------------------------------
[importlinter:contract:quality_tools_isolation]
name = Quality Tools Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    pytest
    _pytest
    pylint
    mypy
    ruff
    vulture
    bandit
    importlinter
    tach
    deptry
```

## HOW

A passing `lint-imports` proves nothing here: a misspelled name also passes, because forbidden modules that aren't in the graph are skipped. The one-off check below is the test for this step, and it replaces a permanent test on purpose.

Throwaway module content:

```python
import _pytest
import bandit
import deptry
import importlinter
import mypy
import pylint
import pytest
import ruff
import tach
import vulture
```

## ALGORITHM

```
run run_lint_imports_check                 -> must pass with the new contract
create src/mcp_coder/_quality_probe.py     -> imports all ten names
run run_lint_imports_check                 -> quality_tools_isolation must be BROKEN, naming all ten
delete src/mcp_coder/_quality_probe.py
run run_lint_imports_check                 -> must pass again
write the result to pr_info/.commit_message.txt
```

If the contract fails in the first run, or any name is missing from the report in the second, delete the throwaway module, write one line to `pr_info/.blocked.txt` naming the cause, and stop.

## DATA

`pr_info/.commit_message.txt`, with the result as observed:

```
chore(importlinter): add quality_tools_isolation contract

Forbid mcp_coder from importing Python quality tools.

One-off check: a throwaway module under src/mcp_coder/ imported all ten
forbidden names. lint-imports reported the contract broken for each of
pytest, _pytest, pylint, mypy, ruff, vulture, bandit, importlinter, tach
and deptry. The module was then deleted and lint-imports passed.
```

## Checks

- `src/mcp_coder/_quality_probe.py` no longer exists.
- `run_lint_imports_check` passes.
- Run pylint, mypy and pytest as usual. Nothing in them should change, since only `.importlinter` differs.
