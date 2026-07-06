# Step 3 — Anti-drift test (the permanent lock)

> Read `pr_info/steps/summary.md` first. This step adds the regression lock that
> makes the single-source guarantee enforceable forever. One commit.

## Objective

Add a test that walks the **built parser tree** and asserts:
1. every non-group, non-suppressed **leaf** command appears in `get_help_text()`;
2. each leaf's `help=` string equals its shown description
   (`COMMAND_DESCRIPTIONS[display]`);
3. no group parser (`commit`, `check`, `gh-tool`, `git-tool`, `vscodeclaude`) or
   suppressed `help` leaf is listed;
4. `COMMAND_DESCRIPTIONS` keys and the tree's leaf set are identical (no orphans
   either way), and every key is placed in exactly one `COMMAND_CATEGORIES` entry.

This permanently prevents omissions like the previously-missing
`checkout-issue-branch` and any future wording drift.

## WHERE

- **Create** `tests/cli/test_help_anti_drift.py`

Test-only imports (no cycle, allowed in tests):
```python
from mcp_coder.cli.main import create_parser
from mcp_coder.cli.command_catalog import (
    COMMAND_CATEGORIES,
    COMMAND_DESCRIPTIONS,
)
from mcp_coder.cli.commands.help import get_help_text
```

## WHAT — helper + tests

```python
def collect_leaves(
    parser: argparse.ArgumentParser,
) -> dict[str, str | None]:
    """Return {display_name: help_string} for every leaf subparser."""
```

Tests (each a plain function):
- `test_every_leaf_is_described` — leaves ⊆ `COMMAND_DESCRIPTIONS`, and
  `help == COMMAND_DESCRIPTIONS[name]` for each leaf.
- `test_every_description_is_a_real_leaf` — `COMMAND_DESCRIPTIONS` keys == leaf
  set (catches stale entries).
- `test_every_leaf_rendered_in_overview` — `name` and its description both appear
  in `get_help_text()`.
- `test_group_and_suppressed_not_listed` — `"help"` and the five group names are
  absent from `COMMAND_DESCRIPTIONS` and from the leaf set.
- `test_every_description_categorized` — every key appears in exactly one
  `COMMAND_CATEGORIES` bucket; category names/order match the settled layout.

## HOW / ALGORITHM — `collect_leaves`

Uses public `parser.prog` for display names; reads subparser structure via
argparse attributes (acceptable in **test** code — the "no internals in the
renderer" rule from the issue does not apply here).

**Suppression must be filtered explicitly — it is NOT free.** A subparser added
with `help=argparse.SUPPRESS` is *not* absent from the parser: it still appears
in `action.choices` (key `"help"`) and in `action._choices_actions` with its
help text set to `argparse.SUPPRESS` (the literal `"==SUPPRESS=="`). So the walk
would otherwise collect the suppressed `help` command and break the anti-drift
assertions. `collect_leaves` therefore must skip any entry whose captured help is
`argparse.SUPPRESS` (equivalently, skip the known suppressed `help` command).

```
def collect_leaves(parser):
    out = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            help_by_name = {ca.dest: ca.help for ca in action._choices_actions}
            for name, sub in action.choices.items():
                help_text = help_by_name.get(name)
                if help_text == argparse.SUPPRESS:  # suppressed leaf -> skip
                    continue
                if _has_subparsers(sub):          # group -> recurse
                    out.update(collect_leaves(sub))
                else:                              # leaf
                    display = sub.prog[len("mcp-coder "):]
                    out[display] = help_text
    return out
# _has_subparsers(p) = any(isinstance(a, _SubParsersAction) for a in p._actions)
```

## DATA

`collect_leaves` returns `dict[str, str | None]` keyed by display name
(`"gh-tool set-status"`, `"commit auto"`, …). Expected leaf set (19): the keys of
`COMMAND_DESCRIPTIONS` from Step 2.

## Checks

Run and pass `run_pylint_check`, `run_pytest_check` (`-n auto` + fast-exclusion
markers), `run_mypy_check`. Accessing `argparse` "private" attributes in a test
may trigger `pylint` `W0212`; add a scoped
`# pylint: disable=protected-access` on `collect_leaves`. Provide a return-type
annotation so mypy strict passes.

## LLM prompt for this step

> Implement **Step 3** of `pr_info/steps/summary.md` (see
> `pr_info/steps/step_3.md`). Create `tests/cli/test_help_anti_drift.py` with a
> `collect_leaves(parser)` helper that walks the tree built by `create_parser()`
> (deriving display names from `parser.prog`) and the five assertions described:
> every leaf is in `COMMAND_DESCRIPTIONS` with matching `help=`, keys equal the
> leaf set, every leaf renders in `get_help_text()`, group/suppressed parsers are
> excluded, and every description is categorized in `COMMAND_CATEGORIES`. This is
> a test-only commit that must pass against the Step 2 implementation. Run
> `run_pylint_check`, `run_pytest_check` (`-n auto` + fast markers), and
> `run_mypy_check`; fix until all pass. One commit.
