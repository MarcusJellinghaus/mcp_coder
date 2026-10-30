"""Consistency checks between docs/cli-reference.md and the built CLI parsers.

The reference documents behaviour, not option lists, so these tests only pin
what can be checked mechanically: every command has a section and a table row
with the catalog description, and every ``--flag`` the page mentions (in prose
or in examples) exists on the command it is mentioned under.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from mcp_coder.cli.command_catalog import COMMAND_DESCRIPTIONS
from mcp_coder.cli.main import create_parser

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_REFERENCE = REPO_ROOT / "docs" / "cli-reference.md"

_PROG_PREFIX = "mcp-coder "
_HEADING_RE = re.compile(r"^#{2,3} (.+)$", re.MULTILINE)
_TABLE_ROW_RE = re.compile(r"^\| \[`([^`]+)`\]\([^)]*\) \| (.+) \|$", re.MULTILINE)
_FLAG_RE = re.compile(r"(?<![\w-])--[a-z][a-z0-9-]*")


def _doc() -> str:
    return CLI_REFERENCE.read_text(encoding="utf-8")


def _sections() -> dict[str, str]:
    """Map each ``##``/``###`` heading to the text up to the next one."""
    doc = _doc()
    matches = list(_HEADING_RE.finditer(doc))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(doc)
        sections[match.group(1).strip()] = doc[match.end() : end]
    return sections


def _leaf_parsers(
    parser: argparse.ArgumentParser,
) -> dict[str, argparse.ArgumentParser]:  # pylint: disable=protected-access
    """Map display name (e.g. ``gh-tool set-status``) to its leaf parser."""
    leaves: dict[str, argparse.ArgumentParser] = {}
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        for sub in action.choices.values():
            if any(isinstance(a, argparse._SubParsersAction) for a in sub._actions):
                leaves.update(_leaf_parsers(sub))
            else:
                leaves[sub.prog[len(_PROG_PREFIX) :]] = sub
    return leaves


def _long_options(parser: argparse.ArgumentParser) -> set[str]:  # pylint: disable=protected-access
    return {
        option
        for action in parser._actions
        for option in action.option_strings
        if option.startswith("--")
    }


def test_every_command_has_a_section() -> None:
    missing = sorted(set(COMMAND_DESCRIPTIONS) - set(_sections()))
    assert not missing, f"commands without a section in cli-reference.md: {missing}"


def test_command_table_mirrors_the_catalog() -> None:
    rows = dict(_TABLE_ROW_RE.findall(_doc()))
    for name, description in COMMAND_DESCRIPTIONS.items():
        assert name in rows, f"command missing from the table: {name}"
        assert rows[name] == description, (
            f"table description drift for {name}: doc has {rows[name]!r}, "
            f"catalog has {description!r}"
        )


def test_table_lists_only_real_commands() -> None:
    unknown = sorted(
        name
        for name, _ in _TABLE_ROW_RE.findall(_doc())
        if name not in COMMAND_DESCRIPTIONS
    )
    assert not unknown, f"table rows for unknown commands: {unknown}"


def test_flags_in_command_sections_exist() -> None:
    parser = create_parser()
    leaves = _leaf_parsers(parser)
    global_options = _long_options(parser)
    sections = _sections()
    problems: list[str] = []
    for name, leaf in leaves.items():
        if name not in sections:
            continue  # reported by test_every_command_has_a_section
        known = _long_options(leaf) | global_options
        for flag in sorted(set(_FLAG_RE.findall(sections[name]))):
            if flag not in known:
                problems.append(f"{name}: {flag}")
    assert not problems, (
        f"flags in cli-reference.md that do not exist on the command: {problems}. "
        "Fix the doc (the flag was renamed or removed). If the flag belongs to an "
        "external tool, add an explicit allowlist to this test."
    )
