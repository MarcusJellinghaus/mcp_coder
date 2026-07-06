"""Anti-drift lock for the single-source CLI help system.

These tests walk the *built* parser tree from ``create_parser()`` and assert it
stays in lockstep with ``COMMAND_DESCRIPTIONS`` / ``COMMAND_CATEGORIES`` and the
rendered overview. They permanently prevent omissions (like the previously
missing ``gh-tool checkout-issue-branch``) and any future wording drift between
a subparser's ``help=`` and its overview description.

Accessing argparse's "private" attributes is acceptable here: this is test code
walking the parser structure, not the production renderer (which never touches
the parser tree).
"""

from __future__ import annotations

import argparse

from mcp_coder.cli.command_catalog import (
    COMMAND_CATEGORIES,
    COMMAND_DESCRIPTIONS,
)
from mcp_coder.cli.commands.help import get_help_text
from mcp_coder.cli.main import create_parser

# The five parser tree nodes that only group subcommands (no direct action of
# their own) plus the suppressed synthetic ``help`` command. None of these are
# leaves and none may appear in COMMAND_DESCRIPTIONS.
GROUP_NAMES = frozenset({"commit", "check", "gh-tool", "git-tool", "vscodeclaude"})
SUPPRESSED_NAME = "help"

_PROG_PREFIX = "mcp-coder "


def _has_subparsers(parser: argparse.ArgumentParser) -> bool:
    """Return True if the parser has a nested subparsers action (i.e. a group).

    Returns:
        True when at least one action is a subparsers action.
    """
    return any(
        isinstance(action, argparse._SubParsersAction) for action in parser._actions
    )


def collect_leaves(
    parser: argparse.ArgumentParser,
) -> dict[str, str | None]:  # pylint: disable=protected-access
    """Return {display_name: help_string} for every leaf subparser.

    Recurses through group subparsers, skips ``argparse.SUPPRESS`` leaves, and
    derives display names from each subparser's ``prog`` (stripping the
    ``"mcp-coder "`` prefix) so no private naming state is assumed.

    Returns:
        Mapping of display name to the leaf's ``help=`` string.
    """
    out: dict[str, str | None] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            help_by_name = {ca.dest: ca.help for ca in action._choices_actions}
            for name, sub in action.choices.items():
                help_text = help_by_name.get(name)
                if help_text == argparse.SUPPRESS:  # suppressed leaf -> skip
                    continue
                if _has_subparsers(sub):  # group -> recurse
                    out.update(collect_leaves(sub))
                else:  # leaf
                    display = sub.prog[len(_PROG_PREFIX) :]
                    out[display] = help_text
    return out


def test_every_leaf_is_described() -> None:
    """Every leaf is in COMMAND_DESCRIPTIONS with a matching help= string."""
    leaves = collect_leaves(create_parser())
    for name, help_text in leaves.items():
        assert name in COMMAND_DESCRIPTIONS, f"Leaf not described: {name}"
        assert help_text == COMMAND_DESCRIPTIONS[name], (
            f"help= drift for {name}: parser has {help_text!r}, "
            f"catalog has {COMMAND_DESCRIPTIONS[name]!r}"
        )


def test_every_description_is_a_real_leaf() -> None:
    """COMMAND_DESCRIPTIONS keys equal the leaf set (no orphans either way)."""
    leaves = collect_leaves(create_parser())
    assert set(COMMAND_DESCRIPTIONS) == set(leaves)


def test_every_leaf_rendered_in_overview() -> None:
    """Each leaf name and its description appear in get_help_text()."""
    overview = get_help_text()
    leaves = collect_leaves(create_parser())
    for name in leaves:
        assert name in overview, f"Leaf missing from overview: {name}"
        assert (
            COMMAND_DESCRIPTIONS[name] in overview
        ), f"Description missing from overview: {name}"


def test_group_and_suppressed_not_listed() -> None:
    """Group and suppressed parsers stay out of descriptions and the leaf set."""
    leaves = collect_leaves(create_parser())
    excluded = GROUP_NAMES | {SUPPRESSED_NAME}
    for name in excluded:
        assert name not in COMMAND_DESCRIPTIONS, f"Non-leaf in descriptions: {name}"
        assert name not in leaves, f"Non-leaf collected as leaf: {name}"


def test_every_description_categorized() -> None:
    """Every description key appears in exactly one category; layout matches."""
    counts: dict[str, int] = {name: 0 for name in COMMAND_DESCRIPTIONS}
    for _title, names in COMMAND_CATEGORIES:
        for name in names:
            assert name in counts, f"Category lists unknown command: {name}"
            counts[name] += 1

    for name, count in counts.items():
        assert count == 1, f"{name} categorized {count} times (expected exactly 1)"

    category_titles = [title for title, _names in COMMAND_CATEGORIES]
    assert category_titles == [
        "SETUP",
        "BACKGROUND DEVELOPMENT",
        "INTERACTIVE DEVELOPMENT",
        "TOOLS",
    ]
