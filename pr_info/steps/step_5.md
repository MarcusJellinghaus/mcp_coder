# Step 5 — Verdict parser (`verdict.py`)

> References `pr_info/steps/summary.md` §5. A pure, deterministic parser — the strict interface
> between the supervisor's free text and the engine's routing. Repair-retries live in the
> engine (Step 7); this step is parse-only.

## WHERE
- `src/mcp_coder/workflows/review/__init__.py` (new, empty)
- `src/mcp_coder/workflows/review/verdict.py` (new)
- `tests/workflows/review/test_verdict.py` (new)

## WHAT
```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Verdict:
    decision: str                       # "dismiss" | "tasks" | "escalate"
    tasks: list[str] = field(default_factory=list)
    escalate_reason: str | None = None

def parse_verdict(text: str) -> Verdict | None:
    """Extract a fenced JSON verdict from supervisor text; None if invalid."""
```

## HOW
- Pure function; stdlib only (`re`, `json`). No LLM, no IO.
- Consumed by `core.py` (Step 7): `None` triggers a repair retry, then `error`.

## ALGORITHM
```
find last ```json ... ``` fenced block (fallback: first {...} object) in text
json.loads it; on failure -> return None
decision = obj.get("decision"); if decision not in {dismiss,tasks,escalate} -> None
if decision == "tasks" and no non-empty tasks list -> None
if decision == "escalate": escalate_reason = obj.get("escalate_reason")
return Verdict(decision, tasks=[...], escalate_reason=...)
```

## DATA
- Returns `Verdict | None`. `tasks` normalized to `list[str]` (strip empties);
  `escalate_reason` optional str.

## TDD / checks
- Test first (`test_verdict.py`), table-driven: valid `dismiss`; valid `tasks` with a list;
  valid `escalate` with reason; fenced block surrounded by prose; malformed JSON → `None`;
  unknown `decision` → `None`; `tasks` decision with empty/missing list → `None`; extra keys
  ignored.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","verdict"])`, then pylint + mypy.

## LLM prompt for this step
> Implement Step 5 of `pr_info/steps/summary.md`. Create the package
> `src/mcp_coder/workflows/review/__init__.py` and `verdict.py` with a frozen `Verdict`
> dataclass (`decision`, `tasks`, `escalate_reason`) and a pure `parse_verdict(text) ->
> Verdict | None` that extracts the last fenced ```json block, validates `decision` ∈
> {dismiss,tasks,escalate}, requires a non-empty `tasks` list for the `tasks` decision, and
> returns `None` on any malformed/invalid input. Write the table-driven tests in
> `tests/workflows/review/test_verdict.py` first (valid cases, prose-wrapped block, malformed
> JSON, unknown decision, empty tasks). stdlib only. Run verdict tests, pylint, mypy.
