# Step 1 — `severity.py`: pure severity parser

See `pr_info/steps/summary.md` (§"Two-layer severity enforcement"). This step adds the
deterministic **backstop** primitive: a pure function that reports the highest severity
present in a reviewer report. No IO, no LLM — the sibling of `verdict.py`.

## WHERE
- New: `src/mcp_coder/workflows/review/severity.py`
- New test: `tests/workflows/review/test_severity.py`
- Optional export: add `max_severity` to `src/mcp_coder/workflows/review/__init__.py`.

## WHAT
```python
def max_severity(report: str) -> str | None:
    """Return the highest severity token in a reviewer report, or None."""
```

## HOW
- Stdlib only (`re`). Mirror `verdict.py`'s module style/docstring.
- The reviewer contract is `file:line — SEVERITY — desc` with
  `critical|high|medium|low`. Scan the whole report for any severity token and keep the
  maximum by rank.

## ALGORITHM
```
_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
_RE = re.compile(r"\b(critical|high|medium|low)\b", re.IGNORECASE)
best, best_rank = None, 0
for m in _RE.finditer(report):
    rank = _RANK[m.group(1).lower()]
    if rank > best_rank: best, best_rank = m.group(1).lower(), rank
return best
```
Safety bias: a permissive scan can only *over*-detect `critical`/`high` (→ keep `tasks`);
it can never miss one that is present, so it never wrongly downgrades a real finding.

## DATA
Returns one of `"critical"`, `"high"`, `"medium"`, `"low"`, or `None` when no severity
token appears (the fail-open signal consumed by the Step 5 backstop).

## TDD
Write `test_severity.py` first:
- single findings of each level → that level;
- mixed report → the highest present (e.g. one `low` + one `high` → `"high"`);
- `"NO FINDINGS"` / empty / prose without a severity token → `None`;
- case-insensitivity (`HIGH` → `"high"`).

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md`). Create
> the pure module `src/mcp_coder/workflows/review/severity.py` exposing
> `max_severity(report: str) -> str | None`, following the style of the existing
> `verdict.py`. Write `tests/workflows/review/test_severity.py` first (all levels, mixed,
> none/empty/prose, case-insensitivity), then implement. No IO, no LLM. Run pylint, pytest
> (`-n auto -m "not ... integration"`) and mypy; all must pass. One commit.
