# Step 1: Add `--list-mcp-tools` flag to verify parser

## LLM Prompt

> Read `pr_info/steps/summary.md` for context on issue #639. Then implement Step 1:
> Add the `--list-mcp-tools` store_true flag to the verify subparser in `parsers.py`.
> Write tests first (TDD), then the implementation. Run all three code quality checks after changes.

## WHERE

- **Test:** `tests/cli/commands/test_verify_parser.py`
- **Impl:** `src/mcp_coder/cli/parsers.py` (inside `add_verify_parser()`)

## WHAT

No new functions. Add one `add_argument` call to the existing verify parser.

### Test signatures (add to `TestVerifyParser`)

```python
def test_list_mcp_tools_flag_default_false(self) -> None: ...
def test_list_mcp_tools_flag_set(self) -> None: ...
```

## HOW

In `add_verify_parser()`, after the existing `--mcp-config` argument, add:

```python
verify_parser.add_argument(
    "--list-mcp-tools",
    action="store_true",
    help="List MCP tools with descriptions grouped by server",
)
```

## DATA

- `args.list_mcp_tools`: `bool`, defaults to `False`

## ALGORITHM

N/A — declarative argument definition.

## Commit

```
Add --list-mcp-tools flag to verify parser (#639)
```
