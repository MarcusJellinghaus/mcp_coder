"""The ``.mcp-file-access`` rules file and the ``.scratch/`` gitignore line.

Both are written by ``mcp-coder init`` only. The vscodeclaude session launch
shares ``GITIGNORE_ENTRY`` with init and must never gitignore ``.scratch/``,
so the ``.scratch/`` line has its own writer here.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from ...mcp_workspace import (
    FileAccess,
    get_file_access,
    is_path_gitignored,
    validate_access_rules,
)
from ...utils.log_utils import OUTPUT
from ...utils.text_io import write_lf_text

logger = logging.getLogger(__name__)

FILE_ACCESS_RULES_FILE = ".mcp-file-access"

FILE_ACCESS_HEADER = (
    "# mcp-workspace file access rules - see mcp-workspace docs/file-access.md\n"
    "# <level> <gitignore pattern>; levels: read-only, read-write; last match wins\n"
)

# Not .mcp.linux.json / .mcp.macos.json: target repos gitignore them, where a
# read-only rule would expose them to MCP reads.
FILE_ACCESS_TEMPLATE_RULES: tuple[tuple[str, str], ...] = (
    ("read-only", "/.vscodeclaude_status.txt"),
    ("read-only", "/.mcp.json"),
    ("read-only", "/.claude/settings.json"),
    ("read-only", "/.claude/settings.local.json"),
    ("read-write", "/.scratch/"),
)

SCRATCH_GITIGNORE_BLOCK = (
    "# Scratch files for LLM sessions: MCP-writable via .mcp-file-access, "
    "never committed\n"
    ".scratch/\n"
)

# Path checked for read-write access before .scratch/ is gitignored
_SCRATCH_PROBE = ".scratch/x"
_SCRATCH_SPELLINGS = frozenset({".scratch", ".scratch/", "/.scratch", "/.scratch/"})

_LEVEL_ACCESS = {
    "read-only": FileAccess.READ_ONLY,
    "read-write": FileAccess.READ_WRITE,
}


def format_rule(level: str, pattern: str) -> str:
    """Format one rules-file line, levels padded to one column.

    Returns:
        The rule line without a line break.
    """
    return f"{level:<11} {pattern}"


def file_access_template() -> str:
    """Return the content of a newly created rules file.

    Returns:
        Header comment plus every template rule, LF line breaks.
    """
    rules = "".join(
        format_rule(level, pattern) + "\n"
        for level, pattern in FILE_ACCESS_TEMPLATE_RULES
    )
    return FILE_ACCESS_HEADER + rules


def _normalise_pattern(pattern: str) -> str:
    """Normalise a pattern for the "already present" check.

    Returns:
        The pattern without whitespace, case-folded on win32.
    """
    compact = "".join(pattern.split())
    return compact.casefold() if sys.platform == "win32" else compact


def _existing_patterns(text: str) -> set[str]:
    """Collect the normalised patterns of every rule line in *text*.

    Returns:
        Normalised patterns; comment, blank and malformed lines are skipped.
    """
    patterns: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            patterns.add(_normalise_pattern(parts[1]))
    return patterns


def _probe_path(pattern: str) -> str:
    """Return a project-relative path a template pattern applies to.

    Returns:
        The pattern without its leading ``/``; a path inside it for a
        directory pattern.
    """
    rel = pattern.lstrip("/")
    return rel + "x" if rel.endswith("/") else rel


def _warn_overridden_rules(project_dir: Path, missing: list[tuple[str, str]]) -> None:
    """Warn for each template path an existing rule gives a different level.

    Appended rules come last and win (last match wins), so they override
    such a user rule. A user rule is detected when the path's access today
    differs from the gitignore default; one that grants the default level is
    not detected.
    """
    for level, pattern in missing:
        probe = _probe_path(pattern)
        after = _LEVEL_ACCESS[level]
        try:
            before = get_file_access(probe, project_dir)
            ignored = is_path_gitignored(probe, project_dir)
        except (OSError, ValueError) as e:
            logger.warning("Could not check existing rules for %s: %s", probe, e)
            continue
        default = FileAccess.HIDDEN if ignored else FileAccess.READ_WRITE
        if before not in (default, after):
            logger.warning(
                "%s: an existing rule gives %s %s; the appended rule '%s' "
                "overrides it (last match wins)",
                FILE_ACCESS_RULES_FILE,
                probe,
                before.name,
                format_rule(level, pattern),
            )


@dataclass(frozen=True)
class RulesOutcome:
    """Result of the rules-file step.

    Attributes:
        ok: False when the rules file could not be read or written.
        changed: True when the rules file was created or extended.
        skip_reason: Why the ``.scratch/`` line must not be written; empty
            when it may be.
    """

    ok: bool
    changed: bool
    skip_reason: str


def _invalid(problem: str) -> RulesOutcome:
    """Report an invalid rules file, which is left untouched.

    Returns:
        An outcome that succeeds but skips the ``.scratch/`` line.
    """
    logger.warning(
        "%s is invalid and was left unchanged: %s", FILE_ACCESS_RULES_FILE, problem
    )
    logger.log(OUTPUT, "File access rules: invalid (%s)", problem)
    return RulesOutcome(ok=True, changed=False, skip_reason="rules file invalid")


def _append_missing_rules(project_dir: Path, rules_path: Path) -> int:
    """Append each template rule whose pattern the rules file lacks.

    Returns:
        The number of rules appended.
    """
    text = rules_path.read_bytes().decode("utf-8-sig")
    present = _existing_patterns(text)
    missing = [
        (level, pattern)
        for level, pattern in FILE_ACCESS_TEMPLATE_RULES
        if _normalise_pattern(pattern) not in present
    ]
    if not missing:
        return 0
    _warn_overridden_rules(project_dir, missing)
    addition = "".join(format_rule(level, pattern) + "\n" for level, pattern in missing)
    # Never glue onto a last line that lacks its newline
    if text and not text.endswith("\n"):
        addition = "\n" + addition
    write_lf_text(rules_path, addition, append=True)
    return len(missing)


def ensure_file_access_rules(project_dir: Path) -> RulesOutcome:
    """Create the rules file, or append the template rules it lacks.

    An invalid file is left byte-identical.

    Args:
        project_dir: Target project root.

    Returns:
        What happened, for the exit code and the ``.scratch/`` step.
    """
    if problems := validate_access_rules(project_dir):
        return _invalid("; ".join(problems))

    rules_path = project_dir / FILE_ACCESS_RULES_FILE
    try:
        if rules_path.exists():
            added = _append_missing_rules(project_dir, rules_path)
            if added:
                logger.log(OUTPUT, "File access rules: %d rules added", added)
            else:
                logger.log(OUTPUT, "File access rules: unchanged")
            changed = bool(added)
        else:
            write_lf_text(rules_path, file_access_template())
            logger.log(OUTPUT, "File access rules: created")
            changed = True
    except UnicodeDecodeError:
        return _invalid("is not valid UTF-8")
    except OSError as e:
        logger.warning(
            "Failed to write %s in %s: %s", FILE_ACCESS_RULES_FILE, project_dir, e
        )
        return RulesOutcome(
            ok=False, changed=False, skip_reason="rules file not written"
        )

    return RulesOutcome(ok=True, changed=changed, skip_reason="")


def ensure_scratch_gitignored(
    project_dir: Path, rules: RulesOutcome
) -> tuple[bool, bool]:
    """Add ``.scratch/`` to the project .gitignore when MCP can still write it.

    Written only when the rules step allows it and ``.scratch/`` is
    read-write under the rules. An undecodable .gitignore is left untouched.

    Args:
        project_dir: Target project root.
        rules: Outcome of :func:`ensure_file_access_rules`.

    Returns:
        ``(ok, changed)``: ok is False when the .gitignore could not be read
        or written; changed is True when the line was added.
    """
    if rules.skip_reason:
        logger.log(OUTPUT, "Gitignore: .scratch/ skipped (%s)", rules.skip_reason)
        return True, False

    gitignore = project_dir / ".gitignore"
    try:
        access = get_file_access(_SCRATCH_PROBE, project_dir)
        if access != FileAccess.READ_WRITE:
            logger.log(
                OUTPUT,
                "Gitignore: .scratch/ skipped (.scratch/ is %s under %s)",
                access.name,
                FILE_ACCESS_RULES_FILE,
            )
            return True, False
        existing = (
            gitignore.read_text(encoding="utf-8-sig") if gitignore.exists() else ""
        )
        if _SCRATCH_SPELLINGS & {line.strip() for line in existing.splitlines()}:
            logger.log(OUTPUT, "Gitignore: .scratch/ present")
            return True, False
        addition = SCRATCH_GITIGNORE_BLOCK
        if existing:
            addition = "\n" + addition  # blank line before the new block
            if not existing.endswith("\n"):
                addition = "\n" + addition
        write_lf_text(gitignore, addition, append=True)
    except (OSError, ValueError) as e:
        logger.warning(
            "Failed to add .scratch/ to .gitignore in %s: %s", project_dir, e
        )
        return False, False

    logger.log(OUTPUT, "Gitignore: .scratch/ added")
    return True, True
