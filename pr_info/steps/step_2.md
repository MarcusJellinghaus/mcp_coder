# Step 2: Implement nested rendering in `_format_section`

**Reference:** [summary.md](summary.md)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Implement the nested branch protection rendering in `src/mcp_coder/cli/commands/verify.py`. Add a `_BRANCH_PROTECTION_CHILDREN` frozenset and modify the `_format_section` loop to render children indented at 4 spaces, suppress children when parent fails, and render `strict_mode` without a status symbol. All tests from Step 1 must now pass. Run pylint, pytest (excluding integration markers), and mypy checks — all must pass.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — modify only

## WHAT

| Symbol | Type | Purpose |
|--------|------|---------|
| `_BRANCH_PROTECTION_CHILDREN` | `frozenset[str]` | Identifies the 4 child keys of `branch_protection` |
| `_format_section` (modified) | function | Add nesting logic to existing loop |

## HOW

- Place `_BRANCH_PROTECTION_CHILDREN` right after `_LABEL_MAP` (before `_format_section`)
- Modify the loop inside `_format_section` — no signature changes

## ALGORITHM

```
_BRANCH_PROTECTION_CHILDREN = frozenset({"ci_checks_required", "strict_mode", "force_push", "branch_deletion"})

# Inside _format_section loop, before existing rendering:
bp_ok = None  # track branch_protection parent state

for key, entry in result.items():
    ...existing skip logic...
    if key == "branch_protection":
        bp_ok = entry.get("ok")
        # render normally (2-space indent) — fall through to existing code
    elif key in _BRANCH_PROTECTION_CHILDREN:
        if bp_ok is False:
            continue  # suppress children when parent failed
        # render at 4-space indent
        if key == "strict_mode":
            line = f"    {label:<20s}   {value}"  # no symbol — informational
        else:
            line = f"    {label:<20s} {symbol} {value}"
        lines.append(line)
        continue  # skip the normal 2-space rendering below
    # ...existing 2-space rendering unchanged...
```

## DATA

No new data structures. `_BRANCH_PROTECTION_CHILDREN` is a simple frozenset of 4 strings.

Output format for children (4-space indent, 20-char label column):
```
    CI checks required [OK] 8 checks configured
    Strict mode          enabled
    Force push         [OK] disabled
    Branch deletion    [OK] disabled
```

## Commit

```
feat: render branch protection checks nested in GitHub section (#899)
```
