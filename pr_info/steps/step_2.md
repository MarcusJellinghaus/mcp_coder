# Step 2 — Single-source command descriptions

> Read `pr_info/steps/summary.md` first (esp. "Settled command descriptions" and
> "Design decision"). This step makes the categorized overview and each
> subparser's `help=` share one string. One commit.

## Objective

Remove the second source of truth for command descriptions. Introduce a
`COMMAND_DESCRIPTIONS` dict + centralized ordered `COMMAND_CATEGORIES` map in
`cli/commands/help.py`; render the overview from them; point every leaf
subparser's `help=` at `COMMAND_DESCRIPTIONS`; apply the settled canonical
wording; add the missing `gh-tool checkout-issue-branch`; move `create-plan`'s
failure-label detail into its `--help` epilog; delete the dead
`Category.description`.

## WHERE

- **Modify** `src/mcp_coder/cli/commands/help.py`
- **Modify** `src/mcp_coder/cli/parsers.py`
- **Modify** `src/mcp_coder/cli/gh_parsers.py`
- **Modify** `tests/cli/commands/test_help.py` (rewrite obsolete tests)

## WHAT — new shape in `help.py`

```python
COMMAND_DESCRIPTIONS: dict[str, str] = {
    "init": "Initialize project: create config and deploy Claude skills",
    "verify": "Verify CLI installation, LLM provider, and MLflow configuration",
    "create-plan": "Generate implementation plan for a GitHub issue",
    "implement": "Execute implementation workflow",
    "create-pr": "Create pull request with AI-generated summary",
    "coordinator": "Monitor GitHub issues and dispatch automated workflows",
    "icoder": "Interactive terminal chat for LLM-assisted coding",
    "vscodeclaude launch": "Launch VSCode/Claude session for issues",
    "vscodeclaude status": "Show current VSCode/Claude sessions",
    "prompt": "Send prompt to configured LLM",
    "commit auto": "Auto-generate commit message using LLM",
    "check branch-status": "Check branch readiness status and optionally apply fixes",
    "check file-size": "Check file sizes against maximum line count",
    "gh-tool checkout-issue-branch": "Checkout or create a branch linked to a GitHub issue",
    "gh-tool set-status": "Update GitHub issue workflow status label",
    "gh-tool get-base-branch": "Detect base branch for current feature branch",
    "gh-tool define-labels": "Sync workflow status labels to GitHub",
    "gh-tool issue-stats": "Display issue statistics by workflow status",
    "git-tool compact-diff": "Generate compact git diff suppressing moved-code blocks",
}

# (category_title, ordered command names) — the single readable layout source.
COMMAND_CATEGORIES: list[tuple[str, list[str]]] = [
    ("SETUP", ["init", "verify"]),
    ("BACKGROUND DEVELOPMENT",
     ["create-plan", "implement", "create-pr", "coordinator"]),
    ("INTERACTIVE DEVELOPMENT",
     ["icoder", "vscodeclaude launch", "vscodeclaude status"]),
    ("TOOLS",
     ["prompt", "commit auto", "check branch-status", "check file-size",
      "gh-tool checkout-issue-branch", "gh-tool set-status",
      "gh-tool get-base-branch", "gh-tool define-labels",
      "gh-tool issue-stats", "git-tool compact-diff"]),
]

def get_help_text() -> str: ...  # stays no-arg
```

Delete the `Command` and `Category` NamedTuple classes and all
`Category.description` data.

## HOW — integration

1. `help.py`: rewrite `_render_help()` / `get_help_text()` to iterate
   `COMMAND_CATEGORIES`, reading `COMMAND_DESCRIPTIONS[name]` for each row.
   Preserve the existing header, `mcp-coder <version>` line, `Usage:` line,
   `OPTIONS` section (`--version`, `--log-level LEVEL`), category headers, column
   alignment, and footer (tests assert these).
2. `parsers.py` / `gh_parsers.py`: add
   `from .commands.help import COMMAND_DESCRIPTIONS`
   (mirrors the existing `from .commands.set_status import ...` import) and change
   each **leaf** subparser's `help=` to `COMMAND_DESCRIPTIONS["<display-name>"]`.
   Use the full display name as the key (e.g. `"vscodeclaude launch"`,
   `"gh-tool set-status"`, `"commit auto"`).
3. Group parsers (`commit`, `check`, `gh-tool`, `git-tool`, `vscodeclaude`) and
   the suppressed `help` parser keep their current `help=` (group help /
   `argparse.SUPPRESS`) — they are NOT in the catalog.
4. `create-plan`: set leaf `help=COMMAND_DESCRIPTIONS["create-plan"]` and add
   `epilog="Sets failure labels and posts comments on error."` (with
   `formatter_class=WideHelpFormatter`, already present).

## ALGORITHM — `_render_help()`

```
width = max(len(name) for _, names in COMMAND_CATEGORIES for name in names)
lines = [header, version, "", usage, "", OPTIONS block...]
for title, names in COMMAND_CATEGORIES:
    lines += ["", title]
    for name in names:
        lines.append(f"  {name:<{width}}  {COMMAND_DESCRIPTIONS[name]}")
lines += ["", footer]
return "\n".join(lines)
```

## DATA

`get_help_text() -> str`. `COMMAND_DESCRIPTIONS: dict[str, str]`,
`COMMAND_CATEGORIES: list[tuple[str, list[str]]]`. No import cycle: `help.py`
imports only `__version__`; parsers import `COMMAND_DESCRIPTIONS` from `help.py`.

## TDD — rewrite `tests/cli/commands/test_help.py`

Keep passing (adjust to new structure where they read data): version header,
`OPTIONS` section, category headers, usage line, footer, no-github-url, header.
Rewrite for the new shape:
- `test_command_categories_contains_all_commands`: assert 4 categories, all 19
  display names present (including `gh-tool checkout-issue-branch`), `"help"`
  absent, and TOOLS order matches the settled list.
- `test_help_text_has_all_commands`: iterate `COMMAND_DESCRIPTIONS`; each name +
  its description appear in `get_help_text()`.
- Remove/replace `test_help_text_no_category_descriptions` (field deleted).
- Column-alignment test: recompute `width` from the new structure.

## Checks

Run and pass `run_pylint_check`, `run_pytest_check` (`-n auto` + fast-exclusion
markers), `run_mypy_check`. Also run `run_lint_imports_check` / `run_tach_check`
to confirm the `parsers → commands.help` import is allowed (fallback per summary
if tach objects). Then verify `create_parser()` in `main.py` is untouched.

## LLM prompt for this step

> Implement **Step 2** of `pr_info/steps/summary.md` (see
> `pr_info/steps/step_2.md`). Using MCP workspace tools: in
> `src/mcp_coder/cli/commands/help.py` add `COMMAND_DESCRIPTIONS` and the
> centralized ordered `COMMAND_CATEGORIES` map exactly as specified, delete the
> `Command`/`Category` NamedTuples and `Category.description`, and render
> `get_help_text()` (no-arg) from them. Point every leaf subparser's `help=` in
> `parsers.py` / `gh_parsers.py` at `COMMAND_DESCRIPTIONS[...]`, applying the
> settled canonical wording, adding `gh-tool checkout-issue-branch`, and moving
> `create-plan`'s failure-label detail into its `--help` epilog. Follow TDD by
> rewriting `tests/cli/commands/test_help.py` for the new shape first. Do not
> modify `main.py`. Run `run_pylint_check`, `run_pytest_check` (`-n auto` + fast
> markers), `run_mypy_check`, and `run_tach_check`; fix until all pass. One
> commit.
