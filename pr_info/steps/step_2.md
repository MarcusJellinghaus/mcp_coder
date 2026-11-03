# Step 2: Tracker classifier; prerequisites only classify

See `pr_info/steps/summary.md` (§1, §2 row 1 of issue #1093).

## WHERE
- New: `src/mcp_coder/workflow_utils/task_tracker_classify.py`
- Modified: `src/mcp_coder/workflow_utils/task_tracker.py` (remove `validate_task_tracker`)
- Modified: `src/mcp_coder/workflows/implement/prerequisites.py` (`check_prerequisites`)
- Tests: new `tests/workflow_utils/test_task_tracker_classify.py`, new fixture
  `tests/workflow_utils/test_data/populated_tracker.md`; update
  `tests/workflow_utils/test_task_tracker_validation.py` and `tests/workflows/implement/test_prerequisites.py`

## WHAT
```python
TRACKER_LABEL = "pr_info/TASK_TRACKER.md"
EXPECTED_FORMAT: str  # skeleton: "## Tasks", "### Step 1: <title>", "- [ ] <sub-task>", "## Pull Request", "- [ ] <PR task>"

class TrackerState(Enum):
    MISSING = "missing"; INVALID = "invalid"; EMPTY = "empty"; POPULATED = "populated"

@dataclass(frozen=True)
class _Line:
    number: int            # 1-based file line
    section: str           # "preamble" | "instructions" | "tasks" | "pull_request" | "other"
    header: str | None     # stripped header line, None if not a header
    step: int | None       # line number of the enclosing strict step header, else None
    checked: bool | None   # None = not a checkbox
    name: str              # _normalize_task_name(_clean_task_name(line)) for checkboxes, else ""

def _scan_tracker(content: str) -> list[_Line]: ...
def classify_tracker_content(content: str) -> tuple[TrackerState, list[str]]: ...
def classify_task_tracker(folder_path: str = "pr_info") -> tuple[TrackerState, list[str]]: ...
def describe_violations(violations: list[str]) -> str: ...  # lines + "Tasks must be grouped ..." + EXPECTED_FORMAT
```
`STEP_HEADER_PATTERN = re.compile(r"^### Step \d+: \S")`. Checkbox detection uses
`_is_task_line`; names use `_clean_task_name` / `_normalize_task_name` from `task_tracker.py`.

## HOW
- `_scan_tracker` skips HTML comment lines, including multi-line `<!-- ... -->`.
  Headers: `re.match(r"^(#{1,6})\s+(.*)", line.strip())`.
- Sections: a level-2 header with exact text "Instructions for LLM" → instructions;
  "Tasks" → tasks; "Pull Request" → pull_request.
  While in tasks, the section ends on the same headers as the step-1 parser: any header with
  two or more `#` (`##`, `###`, `####`, ...) whose whole text is "Pull Request"
  (case-insensitive) switches to pull_request and counts as the `## Pull Request` section.
  Every other header inside tasks keeps the section "tasks" and is a violation unless it is a
  strict step header. After pull_request, the next `##` header switches to "other".
  Outside `## Tasks`, every level-2 header ends the current section; a level-2 header that is
  not Tasks or Pull Request (or Instructions for LLM) starts an "other" section. So a
  `## Step N` header after `## Instructions for LLM` leaves "instructions" and its `[x]` lines count.
  `step` is reset on every `##` header and on the header that ends tasks.
- `check_prerequisites`: keep the existing missing-file check (MISSING → `return False`).
  Then `state, violations = classify_task_tracker(str(pr_info_path))`. If INVALID:
  `logger.warning("Invalid task tracker structure; prep will try to repair it:\n%s", describe_violations(violations))`.
  Return True for EMPTY / POPULATED / INVALID. Remove the `validate_task_tracker` import and
  the `TaskTrackerSectionNotFoundError` handling.
- Delete `validate_task_tracker` from `task_tracker.py`. `has_implementation_tasks` stays until step 5.

## ALGORITHM (`classify_tracker_content`)
```
lines = _scan_tracker(content); v = []
if no "tasks" section: v += ["... no '## Tasks' section"]
for l in tasks: non-step header -> v; checkbox with step None -> one violation at the first line, "(K checkboxes affected)"
for strict step header outside tasks -> v;  for each step in tasks without checkbox -> v
if not v and tasks has a section and no checkbox/header in tasks: return EMPTY, []
if no step in tasks -> v;  no pull_request section -> v;  pull_request without checkbox -> v
return (INVALID, v) if v else (POPULATED, [])
```
`classify_task_tracker`: if the file is missing → `(MISSING, [])`; else read it and classify.

## DATA
Violation string: `"pr_info/TASK_TRACKER.md line 26: checkbox found outside any '### Step N:' section (6 checkboxes affected)"`.

## Tests (write first)
- Template (`TASK_TRACKER_TEMPLATE`) → EMPTY. Rewrite `TestTaskTrackerTemplate::test_template_is_valid`
  in `test_task_tracker_validation.py` to assert this; remove other `validate_task_tracker` tests there.
- `populated_tracker.md` (content of `git show f9fce18:pr_info/TASK_TRACKER.md`) → POPULATED,
  even though the instruction block has checkboxes.
- INVALID: #1146 shape (two flat checkboxes in `## Tasks`, empty `## Pull Request`); #1085
  shape (flat `- [x] [Step N — ...]` list); flat list under `### Implementation Steps`;
  `## Step N` tracker without `## Tasks` (no exception); checkbox before the first step;
  step without checkboxes; `### Notes`, `## Code Review` and `#### Notes` inside `## Tasks`;
  `### Step N:` after `## Pull Request`; missing `## Pull Request`; `## Pull Request` without checkbox.
- Template + `### Step 1: x` placed after `## Pull Request` → INVALID (not EMPTY).
- Classifier and parser agree on the `## Tasks` end, parametrized over `## Pull Request`,
  `### Pull Request` and `#### Pull Request`: a populated tracker whose PR header uses that
  level classifies as POPULATED, the checkboxes the scanner puts in "tasks" match
  `get_task_counts()` (which reads `_find_implementation_section`), and the checkbox after the
  PR header is in "pull_request".
- No file → MISSING.
- Violations carry file line numbers (assert `"line 26"`-style text for a known fixture).
- `check_prerequisites`: INVALID → True and a WARNING in `caplog`; missing tracker → False.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2 only.
> Create the fixture `tests/workflow_utils/test_data/populated_tracker.md` from
> `git show f9fce18:pr_info/TASK_TRACKER.md` (mcp git tool). If that object is unavailable,
> write one line to `pr_info/.blocked.txt` and stop. Write the classifier tests first, then
> `task_tracker_classify.py`, then switch `check_prerequisites` to the classifier and remove
> `validate_task_tracker` with its tests. Run pylint, pytest (`-n auto`, unit markers) and mypy.
