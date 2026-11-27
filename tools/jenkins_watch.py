#!/usr/bin/env python3
"""Watch Jenkins builds and exit when something needs a look.

First reports the current state: the running builds, else the newest build;
if that one ended badly, it exits at once (skip with --watch-only). Then polls
the newest builds, of one issue or of all, and prints new builds and status
changes. A running build is fine as long as its console log grows (checked
every few minutes; the polls themselves only list builds). Each
finished, stalled or still running build it reports gets its console log saved
and scanned for errors, warnings and the lines that decide a workflow step. A
successful build does not end the watch. All Jenkins
logic lives in ``mcp_coder.utils.jenkins_operations``, so run it with a Python
that has mcp-coder installed (the project venv, as tools/jenkins_watch.sh and
.bat do); the script itself uses only the standard library besides that.

The last line is the result:
    RESULT: idle           no build ran for --idle minutes
    RESULT: problem        a build ended failure, unstable or aborted
    RESULT: stalled        a running build's log did not grow for --stall minutes
    RESULT: heartbeat      a build still runs (and its log grows) after --report minutes
    RESULT: jenkins-error  Jenkins failed every poll for 5 minutes

Exit codes: 0 for every result above except jenkins-error, which exits 3 like
any other Jenkins or configuration failure; 2 for bad arguments.

The scan covers the mcp-coder command's output, between the Executor's
"command execution ===" and "archive after execution ===" lines, and prints
that line range so a reader can open just that part of the saved log. It also
prints the last label change it finds there.

Usage:
    python tools/jenkins_watch.py [--issue N [--repo NAME]] [--job PATH]
        [--interval SECONDS] [--idle MINUTES] [--stall MINUTES] [--report MINUTES]
        [--watch-only]
    python tools/jenkins_watch.py --list [--issue N [--repo NAME]] [--job PATH]
    python tools/jenkins_watch.py --inspect BUILD_NUMBER... [--job PATH]
"""

import argparse
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsClient, JenkinsError
from mcp_coder.utils.jenkins_operations.client import get_jenkins_config
from mcp_coder.utils.user_config import load_config

PROBLEM_STATUSES = frozenset({"failure", "unstable", "aborted"})
MAX_PRINTED_MATCHES = 25
# Warnings can be long and are rarely the cause; errors and decisions print in full.
MAX_WARNING_WIDTH = 200
# Give up after Jenkins failed every poll for this long, whatever the interval.
JENKINS_ERROR_MINUTES = 5
# Only the stall check downloads a running build's log; the client has no cheaper
# way to see its size. Every few minutes is plenty against a stall limit of an hour.
LOG_CHECK_MINUTES = 5
# Jenkins' Text Finder plugin quotes the patterns it searched for, " - ERROR - " included.
IGNORED_PREFIX = "[Text Finder]"
# The Executor script echoes these around the mcp-coder command. Anchored, so the
# echoed script source ("echo command execution ...") does not match.
SECTION_START = re.compile(r"^command execution\s+=+\s*$")
SECTION_END = re.compile(r"^archive after execution\s+=+\s*$")
# Executor display name: "<repo> - #<issue> - <step> - #<build>".
BUILD_NAME = re.compile(r" - #(?P<issue>\d+) - (?P<step>.+) - #\d+$")

# Label changes: mcp-coder's label_transitions, and its set-status command.
LABEL_CHANGE = re.compile(
    r"Successfully updated issue #\d+ label: (?P<change>.+)$|Updated issue #\d+ to (?P<status>\S+)"
)

# Checked in this order, first match wins: decisions before warnings, because the
# review handoff logs its banner and its reason at WARNING level.
LOG_PATTERNS = (
    (
        "error",
        re.compile(
            r" - (ERROR|CRITICAL) - |^ERROR:|Traceback \(most recent call last\)"
        ),
    ),
    (
        "decision",
        re.compile(
            r"Blocked marker found:|REVIEW HANDED OFF| - Reason: |Successfully updated issue #\d+ label:"
            r"|Updated issue #\d+ to |Skipped set-status|Workflow failed|^Finished: "
        ),
    ),
    ("warning", re.compile(r" - WARNING - ")),
)


@dataclass(frozen=True)
class Options:
    """What to watch and for how long. Interval in seconds, the others in minutes."""

    job: str | None
    pattern: re.Pattern[str] | None
    limit: int
    interval: float
    idle: float
    stall: float
    report: float
    log_dir: Path
    watch_only: bool = False


@dataclass(frozen=True)
class LogMatch:
    """One log line worth a look."""

    kind: str
    line_number: int
    text: str


def issue_pattern(issue: int, repo: str | None) -> re.Pattern[str]:
    """Return the display-name regex for one issue.

    Executor builds are named ``<repo> - #<issue> - <step> - #<build>``.

    Args:
        issue: Issue number
        repo: Repository name as in the display name, or None for any repo

    Returns:
        The compiled pattern
    """
    prefix = f"^{re.escape(repo)}" if repo else ""
    return re.compile(f"{prefix} - #{issue} - ")


def changed_builds(
    previous: list[BuildInfo], current: list[BuildInfo]
) -> list[BuildInfo]:
    """Return the builds that are new or changed status.

    Keyed on job and number: the display name changes once a build gets an agent.

    Args:
        previous: Builds of the last poll
        current: Builds of this poll

    Returns:
        Changed builds, in the order of ``current``
    """
    status_before = {(b.job_path, b.number): b.status for b in previous}
    return [b for b in current if status_before.get((b.job_path, b.number)) != b.status]


def log_filename(number: int, display_name: str, saved_at: datetime) -> str:
    """Return the file name for a saved console log.

    The save time keeps a running build's earlier snapshots.

    Args:
        number: Build number
        display_name: Jenkins displayName; issue and step are taken from it
        saved_at: When the log is saved

    Returns:
        E.g. "jenkins_log_43_implement_3174_2026-11-26_19-04-08.txt", or
        "jenkins_log_3174_<time>.txt" for a build without an Executor name
    """
    match = BUILD_NAME.search(display_name)
    issue_step = ""
    if match:
        step = re.sub(r"[^\w-]", "_", match["step"])
        issue_step = f"{match['issue']}_{step}_"
    return f"jenkins_log_{issue_step}{number}_{saved_at:%Y-%m-%d_%H-%M-%S}.txt"


def command_section(log: str) -> tuple[int, int] | None:
    """Return the lines of the mcp-coder command's output in an Executor log.

    Args:
        log: Console log text

    Returns:
        First and last line number (1-based, the markers included); the last is
        the end of the log while the build runs or after a crash. None when the
        command never started.
    """
    lines = log.splitlines()
    start = next((i for i, text in enumerate(lines) if SECTION_START.match(text)), None)
    if start is None:
        return None
    end = next(
        (i for i in range(start + 1, len(lines)) if SECTION_END.match(lines[i])),
        len(lines) - 1,
    )
    return start + 1, end + 1


def scan_log(log: str, first: int = 1, last: int | None = None) -> list[LogMatch]:
    """Find the errors, warnings and deciding lines in a console log.

    Args:
        log: Console log text
        first: First line number to scan (1-based)
        last: Last line number to scan, None for the end of the log

    Returns:
        Matches in log order; each line counts once, under its first kind
    """
    matches = []
    for line_number, text in enumerate(log.splitlines(), start=1):
        if line_number < first or (last is not None and line_number > last):
            continue
        if text.startswith(IGNORED_PREFIX):
            continue
        kind = next((k for k, regex in LOG_PATTERNS if regex.search(text)), None)
        if kind is not None:
            matches.append(LogMatch(kind, line_number, text))
    return matches


def label_change(matches: list[LogMatch]) -> str | None:
    """Return the last label change among the scan's matches.

    Args:
        matches: Result of scan_log

    Returns:
        E.g. "status-06:implementing → status-07:code-review", or the new label
        alone for set-status; None when the label did not change
    """
    for match in reversed(matches):
        found = LABEL_CHANGE.search(match.text)
        if found:
            return found["change"] or found["status"]
    return None


def say(message: str) -> None:
    """Print a timestamped line; flushed so a background run's output file stays current."""
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def describe(build: BuildInfo) -> str:
    """Return a one-line summary of a build."""
    return f"{build.status:<8} #{build.number}  {build.display_name}"


def list_line(build: BuildInfo) -> str:
    """Return a build's line for --list: start time, duration, summary."""
    started = build.timestamp.astimezone()
    duration = f"{build.duration_ms / 60_000:.0f} min" if build.duration_ms else ""
    return f"{started:%Y-%m-%d %H:%M}  {duration:>7}  {describe(build)}"


def inspect_log(
    client: JenkinsClient,
    job_path: str,
    number: int,
    log_dir: Path,
    display_name: str = "",
    saved_at: datetime | None = None,
) -> bool:
    """Save a build's console log (so far, if it still runs) and print what the scan found.

    Args:
        client: Jenkins client
        job_path: Full job path, e.g. "Windows-Agents/Executor"
        number: Build number
        log_dir: Directory for the log file
        display_name: Jenkins displayName, for the file name
        saved_at: Save time for the file name; None for now

    Returns:
        False if the log could not be downloaded or saved
    """
    target = log_dir / log_filename(number, display_name, saved_at or datetime.now())
    try:
        text = client.get_console_output(job_path, number)
        log_dir.mkdir(parents=True, exist_ok=True)
        # newline="": the log already has CRLF; text mode would write CR CR LF on Windows.
        target.write_text(text, encoding="utf-8", newline="")
    except (JenkinsError, OSError) as e:
        print(f"  log download failed: {e}", flush=True)
        return False
    section = command_section(text)
    if section is None:
        where = "no command section, whole log scanned"
        matches = scan_log(text)
    else:
        where = f"command section: lines {section[0]}-{section[1]}"
        matches = scan_log(text, *section)
    counts = ", ".join(
        f"{kind} {sum(m.kind == kind for m in matches)}" for kind, _ in LOG_PATTERNS
    )
    print(f"  log: {target} ({len(text.splitlines())} lines; {where}; {counts})")
    label = label_change(matches)
    if label:
        print(f"  label: {label}")
    for match in matches[:MAX_PRINTED_MATCHES]:
        shown = (
            match.text[:MAX_WARNING_WIDTH] if match.kind == "warning" else match.text
        )
        print(f"  {match.line_number:>6}: {shown}")
    if len(matches) > MAX_PRINTED_MATCHES:
        print(f"  ... {len(matches) - MAX_PRINTED_MATCHES} more, see the log file")
    sys.stdout.flush()
    return True


def watch(
    client: JenkinsClient,
    options: Options,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> str:
    """Poll until a build ends badly, nothing runs for a while, or time runs out.

    Args:
        client: Jenkins client
        options: What to watch and for how long
        sleep: Sleep function, replaced in tests
        now: Monotonic clock in seconds, replaced in tests

    Returns:
        The result, also printed as the last line; see the module docstring
    """

    def list_builds() -> list[BuildInfo]:
        return client.get_recent_builds(
            limit=options.limit, path=options.job, name_pattern=options.pattern
        )

    def running(builds: list[BuildInfo]) -> list[BuildInfo]:
        return [b for b in builds if b.status == "running"]

    def inspect(build: BuildInfo) -> None:
        inspect_log(
            client, build.job_path, build.number, options.log_dir, build.display_name
        )

    def result(name: str, detail: str = "") -> str:
        say(f"RESULT: {name}{detail}")
        return name

    # Per running build: log length at the last check, and when it last grew.
    log_growth: dict[tuple[str, int], tuple[int, float]] = {}
    next_log_check = now()

    def stalled_build(builds: list[BuildInfo]) -> BuildInfo | None:
        nonlocal next_log_check
        if now() < next_log_check:
            return None
        next_log_check = now() + LOG_CHECK_MINUTES * 60
        for build in running(builds):
            length = len(client.get_console_output(build.job_path, build.number))
            seen = log_growth.get((build.job_path, build.number))
            if seen is None or seen[0] != length:
                log_growth[(build.job_path, build.number)] = (length, now())
            elif now() - seen[1] >= options.stall * 60:
                return build
        return None

    start = last_active = now()
    failing_since: float | None = None
    previous = list_builds()
    stalled_build(previous)
    for build in running(previous):
        say(describe(build))
    if not options.watch_only and previous and not running(previous):
        newest = previous[0]
        say(f"newest {describe(newest)}")
        if newest.status in PROBLEM_STATUSES:
            inspect(newest)
            return result("problem")
    target = options.pattern.pattern if options.pattern else "all builds"
    say(
        f"watching {target} in {options.job or 'the whole server'}; {len(previous)} builds known"
    )

    while True:
        if running(previous):
            last_active = now()
            if now() - start >= options.report * 60:
                for build in running(previous):
                    say(f"still {describe(build)}")
                    inspect(build)
                return result("heartbeat")
        if now() - last_active >= options.idle * 60:
            return result(
                "idle", f"; newest {describe(previous[0])}" if previous else ""
            )

        sleep(options.interval)
        try:
            current = list_builds()
            stalled = stalled_build(current)
            failing_since = None
        except JenkinsError as e:
            # Printed at the first and the last failed poll only, so a short interval
            # doesn't fill the output.
            if failing_since is None:
                failing_since = now()
                say(f"Jenkins error: {e}")
            elif now() - failing_since >= JENKINS_ERROR_MINUTES * 60:
                say(f"Jenkins error: {e}")
                return result("jenkins-error")
            continue

        changed = changed_builds(previous, current)
        for build in changed:
            say(describe(build))
            if build.status != "running":
                inspect(build)
        previous = current
        if any(b.status in PROBLEM_STATUSES for b in changed):
            return result("problem")
        if stalled is not None:
            say(f"no new log output for {options.stall:g} min: {describe(stalled)}")
            inspect(stalled)
            return result("stalled")


def build_name(client: JenkinsClient, job: str, number: int) -> str:
    """Return a build's display name, or "" when it cannot be found.

    Args:
        client: Jenkins client
        job: Full job path
        number: Build number

    Returns:
        The display name; "" if the build is not among the newest 100 or Jenkins fails
    """
    pattern = re.compile(rf"(^|\D)#{number}$")
    try:
        builds = client.get_recent_builds(limit=1, path=job, name_pattern=pattern)
    except JenkinsError:
        return ""
    return builds[0].display_name if builds else ""


def configured_executor_job() -> str | None:
    """Return the executor_job_path shared by all coordinator repos, else None."""
    repos = load_config().get("coordinator", {}).get("repos", {})
    paths = {r.get("executor_job_path") for r in repos.values() if isinstance(r, dict)}
    jobs = sorted(p for p in paths if isinstance(p, str) and p.strip())
    return jobs[0] if len(jobs) == 1 else None


def make_client() -> JenkinsClient | None:
    """Create a JenkinsClient from the configuration, or print what is missing."""
    config = get_jenkins_config()
    names = {
        "server_url": "JENKINS_URL",
        "username": "JENKINS_USER",
        "api_token": "JENKINS_TOKEN",
    }
    missing = [env for key, env in names.items() if config.get(key) is None]
    if missing:
        print(f"Jenkins not configured: missing {', '.join(missing)}.", file=sys.stderr)
        return None
    return JenkinsClient(
        str(config["server_url"]), str(config["username"]), str(config["api_token"])
    )


def positive_float(value: str) -> float:
    """Parse a positive number for argparse.

    Args:
        value: Command-line text

    Returns:
        The number

    Raises:
        argparse.ArgumentTypeError: If the text is not a number or not positive
    """
    try:
        number = float(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"invalid number: '{value}'") from e
    if number <= 0:
        raise argparse.ArgumentTypeError(f"must be positive, got {value}")
    return number


def main(argv: list[str] | None = None) -> int:
    """Run the tool.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code, see the module docstring
    """
    parser = argparse.ArgumentParser(description="Watch Jenkins builds.")
    parser.add_argument(
        "--issue", type=int, help="watch one issue's builds (default: all)"
    )
    parser.add_argument("--repo", help="repo name in the display name; needs --issue")
    parser.add_argument(
        "--job", help="job or folder path (default: the configured executor job)"
    )
    parser.add_argument(
        "--limit", type=int, default=30, help="newest N builds (default: 30)"
    )
    parser.add_argument(
        "--interval",
        type=positive_float,
        default=15,
        help="seconds between build listings (default: 15); a running build's log "
        f"is checked every {LOG_CHECK_MINUTES} min",
    )
    parser.add_argument(
        "--idle", type=positive_float, default=20, help="minutes (default: 20)"
    )
    parser.add_argument(
        "--stall",
        type=positive_float,
        default=60,
        help="minutes without new log output before a running build counts as stalled (default: 60)",
    )
    parser.add_argument(
        "--report",
        type=positive_float,
        default=120,
        help="minutes after which a still running build is reported (default: 120)",
    )
    parser.add_argument(
        "--log-dir", type=Path, default=Path(".scratch"), help="(default: .scratch)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="only list the newest --limit builds (of --issue), oldest first, then exit",
    )
    parser.add_argument(
        "--inspect",
        type=int,
        nargs="+",
        metavar="N",
        help="only save and scan these builds' logs, then exit",
    )
    parser.add_argument(
        "--watch-only",
        action="store_true",
        help="skip the initial check of the newest build, e.g. right after a retry",
    )
    args = parser.parse_args(argv)
    if args.repo and args.issue is None:
        parser.error("--repo needs --issue")
    job = args.job or configured_executor_job()
    if args.inspect is not None and job is None:
        parser.error("--inspect needs --job (no single executor job configured)")

    pattern = issue_pattern(args.issue, args.repo) if args.issue is not None else None

    client = make_client()
    if client is None:
        return 3
    if args.inspect is not None:
        if job is None:  # checked above; narrows job to str
            parser.error("--inspect needs --job (no single executor job configured)")
        saved = [
            inspect_log(
                client, job, number, args.log_dir, build_name(client, job, number)
            )
            for number in args.inspect
        ]
        return 0 if all(saved) else 3
    if args.list:
        try:
            builds = client.get_recent_builds(
                limit=args.limit, path=job, name_pattern=pattern
            )
        except JenkinsError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 3
        for build in reversed(builds):
            print(list_line(build))
        return 0
    options = Options(
        job=job,
        pattern=pattern,
        limit=args.limit,
        interval=args.interval,
        idle=args.idle,
        stall=args.stall,
        report=args.report,
        log_dir=args.log_dir,
        watch_only=args.watch_only,
    )
    try:
        return 3 if watch(client, options) == "jenkins-error" else 0
    except JenkinsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    # Logs hold non-ASCII ("→"); a Windows console's cp1252 stdout would raise on them.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.exit(main())
