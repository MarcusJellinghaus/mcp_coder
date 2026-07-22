"""Per-run review log writer.

Each review run appends a human-readable round-by-round log under
``pr_info/{log_stem}_review_log_{n}.md``. The run number ``n`` is allocated by
:func:`next_run_number` (scan existing files, take the max, add one), and each
round is appended as a block by :func:`write_round_log`. This is the review
engine's only file IO helper; it performs no LLM work.
"""

import re
from datetime import date
from pathlib import Path

from .config import ReviewConfig


def next_run_number(project_dir: Path, config: ReviewConfig) -> int:
    """Return the run number for a fresh review log.

    Args:
        project_dir: Repository root; logs live under ``project_dir/pr_info``.
        config: The review workflow config providing ``log_stem``.

    Returns:
        ``1`` when no matching log exists, otherwise one past the highest
        existing run number.
    """
    pr_info = project_dir / "pr_info"
    pattern = re.compile(rf"^{re.escape(config.log_stem)}_review_log_(\d+)\.md$")

    highest = 0
    if pr_info.is_dir():
        for entry in pr_info.iterdir():
            match = pattern.match(entry.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def write_round_log(
    project_dir: Path,
    config: ReviewConfig,
    run_number: int,
    round_number: int,
    findings: str,
    decisions: str,
    changes: str,
    escalate_reason: str | None = None,
) -> Path:
    """Append one round block to the run's review log, creating it if needed.

    On ``round_number == 1`` (and only if the file does not yet exist) a
    top-level header is written first. Every call then appends a
    ``## Round {r}`` block carrying findings, decisions, and changes, plus an
    optional escalate reason.

    Args:
        project_dir: Repository root; the log lives under ``project_dir/pr_info``.
        config: The review workflow config providing ``log_stem``/``name``.
        run_number: The run number allocated by :func:`next_run_number`.
        round_number: 1-based round index within the run.
        findings: Reviewer findings text for this round.
        decisions: Supervisor decisions text for this round.
        changes: Summary of changes applied this round.
        escalate_reason: Reason string rendered only when the round escalates.

    Returns:
        The path of the log file written to.
    """
    path = project_dir / "pr_info" / f"{config.log_stem}_review_log_{run_number}.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    if round_number == 1 and not path.exists():
        parts.append(f"# {config.name} review log {run_number}\n")

    parts.append(f"\n## Round {round_number} — {date.today().isoformat()}\n")
    parts.append(f"**Findings**:\n{findings}\n")
    parts.append(f"**Decisions**:\n{decisions}\n")
    parts.append(f"**Changes**:\n{changes}\n")
    if escalate_reason:
        parts.append(f"**Escalate reason**: {escalate_reason}\n")

    with path.open("a", encoding="utf-8") as handle:
        handle.write("".join(parts))

    return path
