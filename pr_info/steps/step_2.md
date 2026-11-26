# Step 2: formatter-stable `write_round_log`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Write the tests first, then the code. Run pylint, mypy and the fast pytest
> set (`-n auto`). Format, then make exactly one commit.

## WHERE

- `src/mcp_coder/workflows/review/review_log.py`: `write_round_log`
- `tests/workflows/review/test_review_log.py`

## WHAT

Same signature as today:

```python
def write_round_log(project_dir, config, run_number, round_number,
                    findings, decisions, changes, escalate_reason=None) -> Path
```

Output shape (golden; `D` = `date.today().isoformat()`):

```
# review-implementation review log 1

## Round 1 — D

**Findings**:

<findings.strip()>

**Decisions**:

<decisions.strip()>

**Changes**:

<changes.strip()>

**Escalate reason**: <escalate_reason.strip()>
```

The escalate line appears only when `escalate_reason` is truthy. The file ends
with exactly one `\n`. A second round appends
`\n## Round 2 — D\n\n**Findings**:\n\n…` after the existing content.

## HOW

- Keep appending with `write_lf_text(path, text, append=True)`.
- A leading `"\n"` (the blank line before `## Round`) is added when the file
  already has content or when the `# …` header is written in this call. A new
  file without a header (round > 1, missing file) starts directly with `## Round`.
- Callers always pass non-empty text (the report is checked with `.strip()`,
  `changes` is a fixed word, `str(verdict)`), so there is no empty-body
  special case.
- Update the docstring to say the output is stable under a markdown formatter
  (blank line around headings and after block labels).

## ALGORITHM

```
existing = path.exists() and path.stat().st_size > 0
parts = []
if round_number == 1 and not path.exists(): parts.append(f"# {config.name} review log {run_number}\n")
if parts or existing: parts.append("\n")
parts.append(f"## Round {r} — {date}\n\n")
for label, body in (("Findings", findings), ("Decisions", decisions), ("Changes", changes)): parts.append(f"**{label}**:\n\n{body.strip()}\n\n")
if escalate_reason: parts.append(f"**Escalate reason**: {escalate_reason.strip()}\n\n")
write_lf_text(path, "".join(parts).rstrip("\n") + "\n", append=True)
```

## DATA

Returns the log `Path` (unchanged).

## Tests first (in `test_review_log.py`)

- **Golden, one round:** patch `review_log.date` with a stub whose `today()`
  returns `date(2026, 1, 2)`. Write findings `" f \n"`, decisions `"d"`,
  changes `"c"`, and assert the exact file text.
- **Golden, two rounds:** round 1, then round 2 with an escalate reason; exact
  text.
- **Invariants**, parametrised over inputs: plain text; findings starting with
  `"- a\n- b"`; findings ending with a list; leading/trailing blank lines;
  with/without an escalate reason. Check the text after round 1 and again after
  round 2:
  - the file does not start with `\n` and ends with exactly one `\n`;
  - no `\n\n\n` (inputs contain no internal blank runs);
  - each `#`/`##` heading line has a blank line after it, and a blank line
    before it unless it is line 1;
  - each line in `{"**Findings**:", "**Decisions**:", "**Changes**:"}` is
    followed by an empty line;
  - `**Escalate reason**: x` stays inline.
- The existing tests must keep passing, including the `**Escalate reason**:`
  assertion.

## Commit

`fix(review): write round logs a markdown formatter leaves unchanged`
