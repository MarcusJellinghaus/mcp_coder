# Step 1 — Parse range keys strictly and reject overlaps

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`.
> Follow TDD: write the tests first, then change `config.py` until they pass.
> Only touch the files listed under WHERE. Run pylint, pytest (`-n auto`, unit
> markers as in CLAUDE.md) and mypy; all must pass. Run the formatter, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/toolkits/command/config.py`
- `tests/toolkits/command/test_config.py` (class `TestExitCodes`)

## WHAT

In `config.py`:

```python
import re
from itertools import combinations

ExitCodes = dict[int | tuple[int, int], str]
DEFAULT_EXIT_CODES: ExitCodes = {0: "ok", 1: "findings"}   # contents unchanged
_EXIT_CODE_KEY = re.compile(r"([0-9]+)(?:-([0-9]+))?")

def _exit_codes_errors(value: Any) -> tuple[ExitCodes, list[str]]: ...
```

- Annotate `Step.exit_codes` and `_Defaults.exit_codes` as `ExitCodes`.
- No other signatures change. `_parse_defaults` and `_parse_step` keep their
  failure paths (bad command-level table → global error, default kept; bad
  step table → step dropped).

## HOW

- `[0-9]` instead of `\d`: `\d` matches non-ASCII digits.
- `fullmatch` instead of `match`/`$`: `$` matches before a trailing newline.
- `int()` stays inside the existing `try/except ValueError`; on Python 3.11+
  it raises `ValueError` for strings over 4300 digits.
- `toolkit.py` is not changed in this step; `dict.get(int)` still type-checks
  against the wider key type.

## ALGORITHM (`_exit_codes_errors`)

```
if value is not a Mapping: return {}, ["exit_codes must be a table, got ..."]
for key, status in value.items():
    match = _EXIT_CODE_KEY.fullmatch(key) if isinstance(key, str) else None
    try: start, end = int(group1), int(group2 or group1); require match and start <= end
    except ValueError: errors += "exit_codes key must be a code or a range N-M with N <= M, got {key!r}"; continue
    spans.append((key, start, end))
    if status not in STATUSES: errors += existing value message; continue
    table[(start, end) if group2 else start] = status
for (key_a, lo_a, hi_a), (key_b, lo_b, hi_b) in combinations(spans, 2):
    if lo_a <= hi_b and lo_b <= hi_a: errors += "exit_codes key must not overlap another key, got {key_b!r} (overlaps {key_a!r})"
return table, errors
```

(Raise `ValueError` explicitly when `match is None` or `start > end`, so all
key-shape failures share one `except`.)

## DATA

- `"3"` → key `3`; `"1-125"` → key `(1, 125)`; `"3-3"` → key `(3, 3)`.
- Return `(table, errors)`; callers discard `table` when `errors` is non-empty.

## Tests (write first) — `tests/toolkits/command/test_config.py::TestExitCodes`

1. `test_range_key_becomes_tuple`: step `exit_codes = {"0": "ok", "1-125": "findings"}`
   → no problems, `step.exit_codes == {0: "ok", (1, 125): "findings"}`.
2. `test_invalid_table_is_error`, parametrized over `exit_codes` tables; each
   gives at least one `errors_for("check", "quick")` and
   `parsed.steps["check"]["quick"] == []`:
   - malformed keys: `{"+3": "ok"}`, `{"1_0": "ok"}`, `{"-1": "ok"}`,
     `{" 3 ": "ok"}`, `{"3\n": "ok"}`, `{"٣": "ok"}`, `{"1-2-3": "ok"}`, `{"3-": "ok"}`
   - non-string key: `{3: "ok"}`
   - over 4300 digits: `{"9" * 5000: "ok"}`
   - reversed range: `{"5-3": "findings"}`
   - overlaps: `{"1-5": "findings", "4-9": "error"}`, `{"1-5": "findings", "3": "error"}`,
     `{"1": "findings", "01": "error"}`
   - invalid value on a range key: `{"1-5": "great"}`
3. Messages: one assertion that a malformed key's message contains
   `"exit_codes key must be"` and the key's repr; one that an overlap message
   contains `"overlap"` and both keys' reprs.
4. `test_bad_default_range_is_global_error`: command-level
   `exit_codes = {"5-3": "findings"}` with one plain step → one global error,
   and the step's `exit_codes == DEFAULT_EXIT_CODES`.

Existing tests (`test_non_numeric_key_is_error`, `test_never_raises_on_garbage`,
`test_toolkit_describe.py` fragment `"exit_codes key"`) must keep passing
unchanged.

## Done when

Tests pass, pylint/pytest/mypy clean, one commit, e.g.
`feat(toolkit): accept exit_codes range keys and reject overlaps`.
