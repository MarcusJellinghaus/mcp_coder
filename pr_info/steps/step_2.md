# Step 2: CLI parsers — replace `--update-labels` with granular flags

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/cli/parsers.py` — modify 3 parser functions
- `tests/cli/test_parsers.py` — new test class

## WHAT

### Changes in `parsers.py`

In `add_implement_parser()`, `add_create_plan_parser()`, and `add_create_pr_parser()`:

**Remove:**
```python
parser.add_argument(
    "--update-labels",
    action="store_true",
    help="Automatically update GitHub issue labels on success/failure",
)
```

**Add (in each):**
```python
parser.add_argument(
    "--update-issue-labels",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Update GitHub issue labels on success/failure (default: from config)",
)
parser.add_argument(
    "--post-issue-comments",
    action=argparse.BooleanOptionalAction,
    default=None,
    help="Post GitHub comments on workflow failure (default: from config)",
)
```

## HOW
- `BooleanOptionalAction` is available in `argparse` (Python 3.9+, already imported)
- Produces `--update-issue-labels` / `--no-update-issue-labels` and `--post-issue-comments` / `--no-post-issue-comments`
- Default `None` gives three-state: `True`, `False`, `None` (not specified)

## ALGORITHM
No algorithm — purely declarative argparse changes.

## DATA
- `args.update_issue_labels`: `bool | None` — `True` if `--update-issue-labels`, `False` if `--no-update-issue-labels`, `None` if not passed
- `args.post_issue_comments`: `bool | None` — same three-state
- Old `args.update_labels` is **removed** (breaking change)

## TESTS (TDD — write first)

New class `TestBooleanOptionalFlags` in `tests/cli/test_parsers.py`:

1. **`test_update_issue_labels_default_none`** — parse `implement` with no flag → `args.update_issue_labels is None`
2. **`test_update_issue_labels_true`** — parse with `--update-issue-labels` → `args.update_issue_labels is True`
3. **`test_update_issue_labels_false`** — parse with `--no-update-issue-labels` → `args.update_issue_labels is False`
4. **`test_post_issue_comments_default_none`** — parse with no flag → `args.post_issue_comments is None`
5. **`test_post_issue_comments_true`** — parse with `--post-issue-comments` → `True`
6. **`test_post_issue_comments_false`** — parse with `--no-post-issue-comments` → `False`
7. **`test_old_update_labels_flag_removed`** — parse with `--update-labels` → error (SystemExit)
8. **`test_flags_present_on_all_three_parsers`** — verify `implement`, `create-plan`, `create-pr` all have both flags

Tests should import `create_parser` from `mcp_coder.cli.main` and parse subcommand args.

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2: replace --update-labels with BooleanOptionalAction flags in parsers.py.

1. Write tests FIRST in tests/cli/test_parsers.py (new TestBooleanOptionalFlags class)
2. Modify add_implement_parser(), add_create_plan_parser(), add_create_pr_parser() in src/mcp_coder/cli/parsers.py
3. Remove --update-labels, add --update-issue-labels and --post-issue-comments with BooleanOptionalAction
4. Run all code quality checks (pylint, pytest, mypy)
5. Fix any issues until all checks pass

NOTE: This step only changes parser definitions. CLI command tests (test_implement.py, etc.)
construct argparse.Namespace manually and won't break until Step 5 changes the CLI command code.
All checks should stay green after this step.
```

## COMMIT MESSAGE
```
feat: replace --update-labels with granular CLI flags (#661)

Replace --update-labels (store_true) with two BooleanOptionalAction flags:
- --update-issue-labels / --no-update-issue-labels
- --post-issue-comments / --no-post-issue-comments

All default to None (three-state), enabling CLI > config > default priority.
Breaking change: --update-labels is removed with no alias.
```
