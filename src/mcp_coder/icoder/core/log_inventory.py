"""Log inventory: scan icoder JSONL logs and summarise each file."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from mcp_coder.icoder.core.event_log import iter_events
from mcp_coder.icoder.core.types import LogSummary

FIRST_PROMPT_MAX = 80

_FILENAME_RE = re.compile(
    r"^icoder_(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}(?:-\d{1,6})?)$"
)


def _parse_iso_from_name(path: Path) -> datetime | None:
    """Parse the timestamp embedded in an icoder log filename.

    Filenames are of the form ``icoder_<YYYY-MM-DDTHH-MM-SS[-uuuuuu]>.jsonl``.
    Returns ``None`` if the stem does not match.
    """
    match = _FILENAME_RE.match(path.stem)
    if match is None:
        return None
    raw = match.group("ts")
    fmt = "%Y-%m-%dT%H-%M-%S-%f" if raw.count("-") == 5 else "%Y-%m-%dT%H-%M-%S"
    try:
        parsed = datetime.strptime(raw, fmt)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def _mtime_dt(path: Path) -> datetime:
    """Return the file's mtime as a UTC-aware datetime."""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def list_icoder_logs(
    logs_dir: Path | str,
    provider: str | None = None,
) -> list[LogSummary]:
    """Scan ``logs_dir`` for ``icoder_*.jsonl`` files. Sorted newest first.

    If ``provider`` is given, filters out logs whose ``session_start.provider``
    does not match. Logs without a ``session_start`` are included only when
    ``provider`` is ``None``.
    """
    logs_path = Path(logs_dir)
    summaries: list[LogSummary] = []
    for path in logs_path.glob("icoder_*.jsonl"):
        ts = _parse_iso_from_name(path) or _mtime_dt(path)
        prov: str | None = None
        n_turns = 0
        first_prompt = ""
        for event in iter_events(path):
            kind = event.get("event")
            if kind == "session_start":
                raw_provider = event.get("provider")
                prov = raw_provider if isinstance(raw_provider, str) else None
            elif kind == "input_received":
                n_turns += 1
                if not first_prompt:
                    text = event.get("text") or ""
                    if isinstance(text, str):
                        first_prompt = text[:FIRST_PROMPT_MAX]
        if provider is not None and prov != provider:
            continue
        summaries.append(
            LogSummary(
                path=path,
                timestamp=ts,
                provider=prov,
                n_turns=n_turns,
                first_prompt=first_prompt,
            )
        )
    summaries.sort(key=lambda s: s.timestamp, reverse=True)
    return summaries
