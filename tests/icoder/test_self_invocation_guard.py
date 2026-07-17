"""Structural regression tests locking in the no-self-invocation boundary.

See pr_info/steps/summary.md and issue #1040 (I1.2).

Scope caveat: these source-search guards match direct call syntax only
(``.dispatch(``, ``InputSubmitted(``). A second dispatch reached via an alias,
``getattr``, or a line-split call would evade them; that indirection is out of
scope. The realistic threat (routing the stream path straight into
``registry.dispatch``) is a direct call and is caught.
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


def test_input_submitted_constructed_only_in_input_area() -> None:
    """`InputSubmitted(...)` is constructed only inside input_area.py.

    The submit message that reaches handle_input->dispatch is posted only from
    InputArea's Enter-keypress handler. If any other production module were to
    construct/post it, model output could reach dispatch. `InputSubmitted\\(`
    matches both the class definition and the post site — both live in
    input_area.py.
    """
    hits = _call_sites(r"InputSubmitted\(")
    files = {name for name, _ in hits}
    assert files == {"input_area.py"}, f"unexpected InputSubmitted sites: {hits}"
