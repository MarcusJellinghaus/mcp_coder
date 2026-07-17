# Step 1 — Single dispatch call-site invariant + boundary documentation

**Reference:** `pr_info/steps/summary.md`
**Acceptance criteria:** AC3 (primary, load-bearing), AC6 (boundary doc), AC7
**Commit:** one — test + doc edits + checks passing.

## Goal

Lock in the load-bearing invariant: there is **exactly one** production
`registry.dispatch` call site — `AppCore.handle_input`. A future change that
adds a second dispatch site (e.g. routing model output into `dispatch`) must
break this test. Document *why* at the call site and at the module level.

## TDD order

1. Write the source-search test (it passes immediately — the structure already
   holds; that is the regression-lock behaviour).
2. Add the marker comment + module docstring note (documentation "implementation").
3. Run all three quality gates.

## WHERE

- **Create:** `tests/icoder/test_self_invocation_guard.py`
- **Modify:** `src/mcp_coder/icoder/core/app_core.py`

## WHAT

### Test file (new)

```python
"""Structural regression tests locking in the no-self-invocation boundary.

See pr_info/steps/summary.md and issue #1040 (I1.2).
"""
from __future__ import annotations

import re
from pathlib import Path

import mcp_coder.icoder.core.app_core as _app_core_mod

# .../src/mcp_coder/icoder/core/app_core.py -> parents[3] == .../src
SRC_ROOT = Path(_app_core_mod.__file__).resolve().parents[3]


def _call_sites(pattern: str) -> list[tuple[str, int]]:
    """Return (filename, lineno) for every line in src/** matching pattern."""
    rx = re.compile(pattern)
    hits: list[tuple[str, int]] = []
    for path in SRC_ROOT.rglob("*.py"):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if rx.search(line):
                hits.append((path.name, lineno))
    return hits


def test_exactly_one_dispatch_call_site() -> None:
    """Exactly one production `.dispatch(` call site, in app_core.py.

    Load-bearing: routing model/stream output into dispatch would add a
    second call site and break this test. `\\.dispatch\\(` matches only
    call sites — never `def dispatch(` nor the `dispatch_workflow` function.
    """
    hits = _call_sites(r"\.dispatch\(")
    assert len(hits) == 1, f"expected 1 dispatch call site, found: {hits}"
    assert hits[0][0] == "app_core.py"
```

### Production edits (documentation only)

1. **Module docstring** in `app_core.py` — replace the current one-line
   docstring with a boundary note:

```python
"""AppCore — central input router for iCoder. No Textual dependency.

Security boundary (issue #1040, design #1037 §3): this module holds the
ONLY production ``registry.dispatch`` call site (in ``handle_input``). Model
output flows through a separate, one-directional render path
(``stream_llm`` -> ``ICoderApp._handle_stream_event`` -> ``OutputLog``) that
never re-parses text as a command, so a model-emitted ``/skill`` can never
route into a skill's tool context. Any future model-driven command feature
must consciously preserve this gate. Full threat model: I5.6 / #1056.
"""
```

2. **Marker comment** at the dispatch call site in `handle_input`, immediately
   above `response = self._registry.dispatch(text)`:

```python
        # SECURITY BOUNDARY (#1040): the ONLY production dispatch call site.
        # Reached only via on_input_area_input_submitted (human Enter keypress).
        # Model/stream output must never be routed here. A second call site
        # breaks tests/icoder/test_self_invocation_guard.py by design.
        response = self._registry.dispatch(text)
```

## HOW

- Locate `SRC_ROOT` from the imported module's `__file__` (robust whether the
  package is run from the repo or installed) — no hard-coded relative paths.
- The test is a plain unit test (no marker); it runs in the default fast set.

## ALGORITHM (test core)

```
compile regex `\.dispatch\(`
for each *.py under src/:
    for each line: if regex matches, record (filename, lineno)
assert exactly one hit
assert that hit is in app_core.py
```

## DATA

- `_call_sites(pattern) -> list[tuple[str, int]]` — list of `(filename, lineno)`.
- Test asserts `len == 1` and filename `== "app_core.py"`.

## Quality gates

Run pylint, pytest (fast exclusion set, `-n auto`), mypy. `format_all.sh`
before commit.

## LLM prompt

> Implement Step 1 from `pr_info/steps/step_1.md` (context in
> `pr_info/steps/summary.md`). Using the MCP workspace tools only:
> (1) create `tests/icoder/test_self_invocation_guard.py` with the
> `_call_sites` helper and `test_exactly_one_dispatch_call_site` exactly as
> specified; (2) replace the module docstring in
> `src/mcp_coder/icoder/core/app_core.py` with the boundary note, and add the
> marker comment directly above the `self._registry.dispatch(text)` line in
> `handle_input`. Do not change any runtime behaviour. Then run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
> (`extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> and `mcp__tools-py__run_mypy_check`; fix any issues until all pass. This is
> one commit.
