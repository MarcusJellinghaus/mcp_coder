# Step 3: Add Missing Test Method Docstrings (D102)

> **Context:** See [summary.md](summary.md) for overall plan. This is step 3 of 5.

## Goal

Add docstrings to all test methods that are missing them (D102 / pylint C0116).

## Rules Addressed

| Rule | Count | Description |
|---|---|---|
| D102 | ~109 | Missing method docstring |

This also resolves the majority of pylint C0116 violations (~116 total, most overlap with D102).

## WHERE

Test files across:
- `tests/cli/` — ~4 methods
- `tests/llm/` — ~52 methods
- `tests/utils/` — ~53 methods

Identify exact files:
```bash
ruff check tests --select D102
```

## WHAT

No new functions. Add a one-line docstring to each test method describing what it verifies.

## HOW

Pattern for test docstrings:

```python
# Good: describes what the test verifies
def test_parse_empty_input(self):
    """Test that parse returns empty list for empty input."""

# Good: for parameterized/edge case tests
def test_commit_with_special_characters(self):
    """Test commit handles special characters in message."""
```

Guidelines:
- Start with "Test that..." or "Test <subject> <verb>..." 
- One line, ends with period
- Describe the *behavior being verified*, not the implementation
- Keep it concise — the test name already carries context

## ALGORITHM

```
1. Run ruff check to list all D102 violations in tests/
2. For each test method, add a one-line docstring
3. Derive docstring from test name and test body (what it asserts)
4. Run ./tools/format_all.sh
5. Run ruff check, pylint, pytest, mypy to verify
6. Commit
```

## DATA

No data structures. Output: modified test `.py` files with added method docstrings.

## Verification

- `ruff check tests --select D102` — should report 0 violations
- `pylint ./tests --disable=all --enable=C0116` — should report 0
- `pytest` — all pass
- `mypy` — no regressions

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for context.

Execute step 3: Add missing test method docstrings.

1. Run `ruff check tests --select D102` to get the full list of violations
2. For each test method missing a docstring, read the test body to understand what it verifies
3. Add a one-line Google-style docstring: `"""Test that X does Y when Z."""`
4. Keep docstrings concise — derive meaning from the test name and assertions
5. Run ./tools/format_all.sh
6. Verify with ruff check, pylint, pytest, mypy — all must pass
7. Commit the changes

Note: This is the highest-volume step (~109 methods). Work through files systematically, 
one test module at a time.
```
