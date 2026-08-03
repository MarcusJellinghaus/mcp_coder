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
  `critical|high|medium|low`. Match the SEVERITY token **only in its anchored position**
  between the two `—` separators of a finding line, and keep the maximum by rank. Do **not**
  free-scan the whole report: a severity word inside a finding's *description* text (e.g. a
  `low` finding described as "high coupling") or in a summary line (e.g. "No critical/high
  findings") must not count — otherwise the backstop silently never downgrades and AC1 is
  defeated.

## ALGORITHM
```
_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
# Anchor on the finding-line format `file:line — SEVERITY — desc`: the severity
# token must be flanked by the two em-dash separators. This ignores severity
# words that appear in a finding's description or in prose/summary lines.
_RE = re.compile(r"—\s*(critical|high|medium|low)\s*—", re.IGNORECASE)
best, best_rank = None, 0
for m in _RE.finditer(report):
    rank = _RANK[m.group(1).lower()]
    if rank > best_rank: best, best_rank = m.group(1).lower(), rank
return best
```
Safety bias: anchoring to the `— SEVERITY —` position (rather than a free word scan) means a
severity word in description/summary prose can neither *raise* the detected ceiling (which
would wrongly keep `tasks`) nor be mistaken for a finding. Only a real `critical`/`high`
*finding line* keeps `tasks`.

## DATA
Returns one of `"critical"`, `"high"`, `"medium"`, `"low"`, or `None` when no severity
token appears (the fail-open signal consumed by the Step 5 backstop).

## TDD
Write `test_severity.py` first. Use realistic finding lines in the
`file:line — SEVERITY — description` format:
- single findings of each level → that level;
- mixed report → the highest present (e.g. one `low` + one `high` finding line → `"high"`);
- `"NO FINDINGS"` / empty / prose without a finding line → `None`;
- case-insensitivity (`— HIGH —` → `"high"`).
- **Anchoring (defeats the false-positive that would break AC1):**
  - a report whose only finding line is `medium`/`low` but whose *description* text contains
    a severity word (e.g. `src/x.py:10 — low — high coupling between modules`) → `"low"`,
    **not** `"high"`;
  - a report whose finding lines are all `low`/`medium` plus a summary line like
    `Summary: No critical/high findings.` → the max of the finding lines (`"medium"`/`"low"`),
    **not** `"high"` — proving the Step 5 backstop still downgrades to `dismiss` (AC1).

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md`). Create
> the pure module `src/mcp_coder/workflows/review/severity.py` exposing
> `max_severity(report: str) -> str | None`, following the style of the existing
> `verdict.py`. Detect the SEVERITY token only in its anchored `— SEVERITY —` position in a
> `file:line — SEVERITY — desc` finding line (regex flanked by the em-dash separators), NOT a
> free word scan, so a severity word in a description or summary line does not raise the
> ceiling. Write `tests/workflows/review/test_severity.py` first (all levels, mixed,
> none/empty/prose, case-insensitivity, and the anchoring cases: a `low` finding described as
> "high coupling" → `"low"`, and all-`low`/`medium` findings plus a "No critical/high
> findings" summary line → the finding max, never `"high"`), then implement. No IO, no LLM.
> Run pylint, pytest
> (`-n auto -m "not ... integration"`) and mypy; all must pass. One commit.
