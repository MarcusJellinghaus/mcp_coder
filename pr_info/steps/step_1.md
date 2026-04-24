# Step 1: Add `--push` flag to commit parsers

**Ref:** See `pr_info/steps/summary.md` for full context (issue #907).

## WHERE

- `src/mcp_coder/cli/parsers.py` — `add_commit_parsers()` function
- `tests/cli/test_parsers.py` — new test class

## WHAT

Add `--push` as `store_true` argument to both `auto_parser` and `clipboard_parser` inside `add_commit_parsers()`.

## HOW

In `parsers.py`, after the existing arguments for each parser, add:

```python
auto_parser.add_argument(
    "--push",
    action="store_true",
    help="Push to origin after successful commit",
)
```

Same for `clipboard_parser`.

## DATA

- `args.push` → `bool` (defaults to `False`)

## Tests (write first)

Add a `TestCommitPushFlag` class in `tests/cli/test_parsers.py`:

1. `test_commit_auto_accepts_push_flag` — parse `["commit", "auto", "--push"]`, assert `args.push is True`
2. `test_commit_clipboard_accepts_push_flag` — parse `["commit", "clipboard", "--push"]`, assert `args.push is True`
3. `test_commit_auto_push_default_false` — parse `["commit", "auto"]`, assert `args.push is False`
4. `test_commit_clipboard_push_default_false` — parse `["commit", "clipboard"]`, assert `args.push is False`

Follow the existing `_parse` helper pattern used by other test classes in that file.

## Commit

`feat(cli): add --push flag to commit auto and clipboard parsers`

---

## LLM Prompt

> Read `pr_info/steps/summary.md` for overall context, then implement step 1.
> Add `--push` (store_true) to both `auto_parser` and `clipboard_parser` in `src/mcp_coder/cli/parsers.py`.
> Write tests first in `tests/cli/test_parsers.py` following the existing `_parse` helper pattern.
> Run all code quality checks. Commit with message: `feat(cli): add --push flag to commit auto and clipboard parsers`
