# Step 1: `## Tasks` ends only at an exact "Pull Request" header

See `pr_info/steps/summary.md` (§4 of issue #1093).

## WHERE
- `src/mcp_coder/workflow_utils/task_tracker.py`: `_find_implementation_section`
- Tests: `tests/workflow_utils/test_task_tracker_parsing.py`

## WHAT
No signature change. `_find_implementation_section(content: str) -> str`.

## HOW
In the end-marker branch, replace `if "pull request" in header_text:` with
`if header_text == "pull request":`. `header_text` is already stripped of `#` and lowercased,
so this applies at `##`, `###` and `####`. The start-marker logic is unchanged.

## ALGORITHM
```
for each line starting with "##":
    text = lstrip("#").strip().lower()
    if start not found: start at "tasks" / "implementation steps"
    elif text == "pull request": end here
```

## DATA
Unchanged: the section text without its header.

## Tests (write first)
- A tracker with `### Step 3: Add pull request template` followed by `### Step 4: ...` and
  `## Pull Request`: `get_incomplete_tasks` / `get_task_counts` include Step 3's and Step 4's tasks.
- `## Pull Request` and `### Pull Request` still end the section.

## LLM prompt
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1 only:
> write the tests first, then change `_find_implementation_section` so that only a header
> whose whole text is "Pull Request" (case-insensitive) ends the `## Tasks` section. Run
> pylint, pytest (`-n auto`, unit markers excluded) and mypy; all must pass.
