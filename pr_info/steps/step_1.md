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
  between the two separators of a finding line, and keep the maximum by rank. Do **not**
  free-scan the whole report: a severity word inside a finding's *description* text (e.g. a
  `low` finding described as "high coupling") or in a summary line (e.g. "No critical/high
  findings") must not count — otherwise the backstop silently never downgrades and AC1 is
  defeated.
- **Tolerate the formatting a fresh reviewer LLM actually emits** — the backstop is
  deterministic precisely so it does not depend on the LLM formatting its report perfectly.
  Per the contract at `prompts.md:342-343` the `file:line` is backticked and the severities
  are shown as `` `critical` ``/`` `high` ``, so the emitted token may itself be backticked;
  and LLMs routinely normalize the em-dash `—` to one or more ASCII hyphens `-`. The
  separator match must therefore accept **em-dash OR hyphen(s)**, and the severity token must
  match **with or without surrounding backticks**. A regex that only matches a bare word
  flanked by em-dashes would return `None` on hyphen/backticked reports → fail open → the
  backstop never downgrades → AC1 defeated, and (worse) the bare-token unit tests would still
  pass, hiding the gap.

## ALGORITHM
```
_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
# Anchor on the finding-line format `file:line — SEVERITY — desc`, but tolerate the
# formatting the reviewer LLM may emit (see prompts.md:342-343): the separator may be
# an em-dash `—` OR one-or-more ASCII hyphens `-`, and the SEVERITY token (like the
# backticked `file:line`) may be wrapped in backticks. The token must still sit
# BETWEEN the two separators, so a severity word in a description or summary line does
# not count. (Put `-` first in the class so it is a literal, not a range.)
_RE = re.compile(
    r"[-—]+\s*`?(critical|high|medium|low)`?\s*[-—]+",
    re.IGNORECASE,
)
best, best_rank = None, 0
for m in _RE.finditer(report):
    rank = _RANK[m.group(1).lower()]
    if rank > best_rank: best, best_rank = m.group(1).lower(), rank
return best
```
Safety bias: still anchoring to the `<sep> SEVERITY <sep>` position (rather than a free word
scan) means a severity word in description/summary prose can neither *raise* the detected
ceiling (which would wrongly keep `tasks`) nor be mistaken for a finding. Broadening the
separator to hyphens and allowing backticks only ever errs toward *detecting* a real
`critical`/`high` — the safe direction: a missed `high` would wrongly downgrade to `dismiss`
and ship it, whereas a spurious one merely keeps `tasks` (the pre-change behaviour). Only a
real `critical`/`high` *finding line* keeps `tasks`.

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
- **Formatting tolerance (defeats the fail-open that would break AC1 — a bare-em-dash-only
  regex passes these tests while silently no-op'ing in production):**
  - hyphen separators instead of em-dashes: `` `src/x.py:10` - high - desc `` → `"high"`;
  - backticked severity token: `` `src/x.py:10` — `high` — desc `` → `"high"`;
  - both together: `` `src/x.py:10` - `high` - desc `` → `"high"`;
  - a hyphen-separated all-`low`/`medium` report → the finding max (never `None`), proving the
    Step 5 backstop still downgrades to `dismiss`.
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
> `verdict.py`. Detect the SEVERITY token only in its anchored `<sep> SEVERITY <sep>` position
> in a `file:line — SEVERITY — desc` finding line (regex flanked by separators), NOT a free
> word scan, so a severity word in a description or summary line does not raise the ceiling.
> Tolerate the formatting a fresh reviewer LLM may emit (prompts.md:342-343): the separator may
> be an em-dash `—` OR ASCII hyphen(s) `-`, and the severity token may be backticked — a
> bare-em-dash-only regex fails open on such reports and silently defeats AC1. Write
> `tests/workflows/review/test_severity.py` first (all levels, mixed, none/empty/prose,
> case-insensitivity; the formatting-tolerance cases: hyphen-separated and/or backticked
> `high` → `"high"`; and the anchoring cases: a `low` finding described as "high coupling" →
> `"low"`, and all-`low`/`medium` findings plus a "No critical/high findings" summary line →
> the finding max, never `"high"`), then implement. No IO, no LLM.
> Run pylint, pytest
> (`-n auto -m "not ... integration"`) and mypy; all must pass. One commit.
