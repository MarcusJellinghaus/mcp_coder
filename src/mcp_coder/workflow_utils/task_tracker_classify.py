"""Structural classification of TASK_TRACKER.md files.

The parsers in ``task_tracker`` are lenient. This module is strict: it decides
whether a tracker is missing, empty (template only), populated with a valid
``### Step N: <title>`` structure, or invalid, and reports each violation with
its file line number.
"""

import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .task_tracker import _clean_task_name, _is_task_line, _normalize_task_name

TRACKER_LABEL = "pr_info/TASK_TRACKER.md"

STEP_HEADER_PATTERN = re.compile(r"^### Step \d+: \S")
HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.*)")

EXPECTED_FORMAT = """## Tasks

### Step 1: <title>
- [ ] <sub-task>
- [ ] <sub-task>

### Step 2: <title>
- [ ] <sub-task>

## Pull Request
- [ ] <PR task>"""

_LEVEL2_SECTIONS = {
    "instructions for llm": "instructions",
    "tasks": "tasks",
    "pull request": "pull_request",
}


class TrackerState(Enum):
    """Structural state of a task tracker file."""

    MISSING = "missing"
    INVALID = "invalid"
    EMPTY = "empty"
    POPULATED = "populated"


@dataclass(frozen=True)
class _Line:
    """One non-comment line of a tracker file.

    Attributes:
        number: 1-based file line number
        section: "preamble", "instructions", "tasks", "pull_request" or "other"
        header: Stripped header line, None if the line is not a header
        step: Line number of the enclosing strict step header, else None
        checked: Checkbox state, None if the line is not a checkbox
        name: Normalized task name for checkboxes, else ""
    """

    number: int
    section: str
    header: str | None
    step: int | None
    checked: bool | None
    name: str


def _header_parts(header: str) -> tuple[int, str]:
    """Return (level, lowercased text) of a stripped header line."""
    match = HEADER_PATTERN.match(header)
    if not match:
        return 0, ""
    return len(match.group(1)), match.group(2).strip().lower()


def _scan_tracker(content: str) -> list[_Line]:
    """Turn tracker content into per-line records, skipping HTML comments.

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        One record per non-comment line, in file order
    """
    records: list[_Line] = []
    section = "preamble"
    step: int | None = None
    in_comment = False

    for number, line in enumerate(content.split("\n"), start=1):
        stripped = line.strip()

        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            in_comment = "-->" not in stripped[4:]
            continue

        if HEADER_PATTERN.match(stripped):
            level, text = _header_parts(stripped)
            if section == "tasks":
                if level >= 2 and text == "pull request":
                    section = "pull_request"
                    step = None
                elif STEP_HEADER_PATTERN.match(stripped):
                    step = number
                elif level == 2:
                    step = None
            elif level == 2:
                if section == "pull_request":
                    section = "other"
                else:
                    section = _LEVEL2_SECTIONS.get(text, "other")
                step = None
            records.append(_Line(number, section, stripped, step, None, ""))
            continue

        is_task, is_complete = _is_task_line(line)
        if is_task:
            name = _normalize_task_name(_clean_task_name(line))
            records.append(_Line(number, section, None, step, is_complete, name))
        else:
            records.append(_Line(number, section, None, step, None, ""))

    return records


def _is_tasks_opening(record: _Line) -> bool:
    """Return True for the ``## Tasks`` header that opens the section."""
    if record.header is None:
        return False
    return _header_parts(record.header) == (2, "tasks")


def classify_tracker_content(content: str) -> tuple[TrackerState, list[str]]:
    """Classify tracker content and list its structural violations.

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        Tuple of (state, violations); violations is empty unless state is INVALID
    """
    lines = _scan_tracker(content)
    violations: list[str] = []

    tasks = [r for r in lines if r.section == "tasks"]
    has_tasks_section = any(_is_tasks_opening(r) for r in tasks)
    if not has_tasks_section:
        violations.append(f"{TRACKER_LABEL}: no '## Tasks' section")

    step_headers = [
        r for r in tasks if r.header and STEP_HEADER_PATTERN.match(r.header)
    ]
    for record in tasks:
        if (
            record.header
            and not _is_tasks_opening(record)
            and not STEP_HEADER_PATTERN.match(record.header)
        ):
            violations.append(
                f"{TRACKER_LABEL} line {record.number}: header '{record.header}'"
                " inside '## Tasks' is not a '### Step N: <title>' header"
            )

    orphans = [r for r in tasks if r.checked is not None and r.step is None]
    if orphans:
        violations.append(
            f"{TRACKER_LABEL} line {orphans[0].number}: checkbox found outside any"
            f" '### Step N:' section ({len(orphans)} checkboxes affected)"
        )

    for record in lines:
        if (
            record.section != "tasks"
            and record.header
            and STEP_HEADER_PATTERN.match(record.header)
        ):
            violations.append(
                f"{TRACKER_LABEL} line {record.number}: step header"
                f" '{record.header}' is outside '## Tasks'"
            )

    for header in step_headers:
        if not any(r.checked is not None and r.step == header.number for r in tasks):
            violations.append(
                f"{TRACKER_LABEL} line {header.number}: step '{header.header}'"
                " has no checkboxes"
            )

    tasks_content = [
        r
        for r in tasks
        if r.checked is not None or (r.header and not _is_tasks_opening(r))
    ]
    if not violations and not tasks_content:
        return TrackerState.EMPTY, []

    if has_tasks_section and not step_headers:
        violations.append(f"{TRACKER_LABEL}: '## Tasks' has no '### Step N:' sections")

    pull_request = [r for r in lines if r.section == "pull_request"]
    if not pull_request:
        violations.append(f"{TRACKER_LABEL}: no '## Pull Request' section")
    elif not any(r.checked is not None for r in pull_request):
        violations.append(
            f"{TRACKER_LABEL} line {pull_request[0].number}:"
            " '## Pull Request' section has no checkboxes"
        )

    if violations:
        return TrackerState.INVALID, violations
    return TrackerState.POPULATED, []


def classify_task_tracker(
    folder_path: str = "pr_info",
) -> tuple[TrackerState, list[str]]:
    """Classify TASK_TRACKER.md in ``folder_path``.

    Args:
        folder_path: Path to folder containing TASK_TRACKER.md

    Returns:
        Tuple of (state, violations); MISSING if the file does not exist
    """
    tracker_path = Path(folder_path) / "TASK_TRACKER.md"
    if not tracker_path.exists():
        return TrackerState.MISSING, []
    return classify_tracker_content(tracker_path.read_text(encoding="utf-8"))


def describe_violations(violations: list[str]) -> str:
    """Format violations with the expected tracker structure.

    Args:
        violations: Violation strings from the classifier

    Returns:
        Multi-line description for logs, failure messages and prompts
    """
    return (
        "\n".join(violations)
        + "\n\nTasks must be grouped under '### Step N: <title>' headers inside"
        " '## Tasks', followed by a '## Pull Request' section with checkboxes."
        " Expected format:\n\n" + EXPECTED_FORMAT
    )


def _checkboxes(content: str) -> list[_Line]:
    """Return checkbox records outside the instructions section."""
    return [
        r
        for r in _scan_tracker(content)
        if r.checked is not None and r.section != "instructions"
    ]


def has_completed_tasks(content: str) -> bool:
    """Return True if any checkbox outside the instructions section is checked.

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        True if the tracker has at least one ``[x]`` task
    """
    return any(r.checked for r in _checkboxes(content))


def check_restructure(original: str, restructured: str) -> list[str]:
    """Check that a restructured tracker is valid and keeps the original's progress.

    Every ``[x]`` line must survive unchanged, no ``[ ]`` line may be lost, and
    steps containing ``[x]`` may not gain ``[ ]`` lines. ``[ ]`` lines in
    ``## Pull Request`` or in steps without ``[x]`` are not restricted.

    Args:
        original: Tracker content before the restructure
        restructured: Tracker content after the restructure

    Returns:
        Error strings; empty if the restructure is accepted
    """
    state, violations = classify_tracker_content(restructured)
    if state is not TrackerState.POPULATED:
        return violations or [
            f"{TRACKER_LABEL}: restructured tracker is not populated"
            f" (state: {state.value})"
        ]

    old = _checkboxes(original)
    new = _checkboxes(restructured)
    errors: list[str] = []

    old_checked = Counter(r.name for r in old if r.checked)
    new_checked = Counter(r.name for r in new if r.checked)
    if old_checked != new_checked:
        changed = sorted((old_checked - new_checked) + (new_checked - old_checked))
        errors.append(
            "[x] lines added, removed, reworded or toggled: "
            + ", ".join(f"'{name}'" for name in changed)
        )

    old_open = Counter(r.name for r in old if r.checked is False)
    new_open = Counter(r.name for r in new if r.checked is False)
    for name, count in (old_open - new_open).items():
        errors.append(f"'{name}': [ ] line removed, reworded or checked ({count}x)")

    checked_steps = {r.step for r in new if r.checked and r.step is not None}
    open_in_checked_steps = Counter(
        r.name for r in new if r.checked is False and r.step in checked_steps
    )
    for name, count in open_in_checked_steps.items():
        if count > old_open[name]:
            errors.append(
                f"'{name}': {count} unchecked under steps with [x],"
                f" original has {old_open[name]}"
            )

    return errors
