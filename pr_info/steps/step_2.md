# Step 2: Add `install_hint` to Claude CLI verification

> **Context**: See `pr_info/steps/summary.md` for the full plan (Issue #553).

## LLM Prompt

```
Implement Step 2 of Issue #553 (see pr_info/steps/summary.md).

Add an `install_hint` field to the Claude CLI verification `cli_found` entry when the CLI is not found.
The hint should be the docs URL: "https://docs.anthropic.com/en/docs/claude-code"

Follow TDD: write test first in tests/llm/providers/claude/test_claude_cli_verification.py,
then implement in src/mcp_coder/llm/providers/claude/claude_cli_verification.py.

Run all three code quality checks after changes. Commit as one unit.
```

## WHERE

- **Test**: `tests/llm/providers/claude/test_claude_cli_verification.py`
- **Impl**: `src/mcp_coder/llm/providers/claude/claude_cli_verification.py`

## WHAT — Test to Add

Add one test to the existing `TestVerifyClaude` class:

```python
def test_cli_not_found_has_install_hint(self) -> None:
    """When CLI is not found, cli_found entry includes install_hint with docs URL."""
```

Also verify the existing `test_returns_structured_dict` still passes (no `install_hint` when found).

## WHAT — Implementation Change

In `verify_claude()`, when building the `cli_found` entry:

```python
result["cli_found"] = {"ok": basic["found"], "value": "YES" if basic["found"] else "NO"}
if not basic["found"]:
    result["cli_found"]["install_hint"] = "https://docs.anthropic.com/en/docs/claude-code"
```

### Function modified (signature unchanged):

- `verify_claude()` — add `install_hint` to `cli_found` when `ok=False`

## HOW — Integration

Pure data addition — no new imports, no new dependencies.

## ALGORITHM

```
build cli_found entry as before
if not found:
    add install_hint = docs URL
```

## DATA — Return Value Changes

Before (when not found):
```python
{"ok": False, "value": "NO"}
```

After:
```python
{"ok": False, "value": "NO", "install_hint": "https://docs.anthropic.com/en/docs/claude-code"}
```

When `ok=True`, the `install_hint` key is **absent**.
