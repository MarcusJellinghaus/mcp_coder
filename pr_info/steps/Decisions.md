# Decisions — #1294 plan update

Decisions from the plan review discussion after mcp-workspace#350 was merged
(MarcusJellinghaus/mcp-workspace#354).

| # | Topic | Decision |
|---|---|---|
| 1 | Hidden error notes on child rows | Branch-protection child rows show `error` in parentheses when `ok is None` (today: only when `ok is False`). |
| 2 | Error notes on the parent row | The same rule applies to the `branch_protection` parent row only; other `ok=None` rows in the generic branch stay unchanged. |
| 3 | Existing test hiding the parent's 403 error | Keep decision 2 and flip the `"Resource not accessible" not in output` assertion in `test_children_suppressed_when_parent_unverifiable` to expect the error. |
| 4 | Token permissions for the ruleset endpoints | No token test. The docs make no permission statement for `/rules/branches/{b}` or `/rulesets` and describe only the merge behaviour; step 2 has no permission gate. |
| 5 | Step 1 test changes | Result dicts use the upstream key order (`require_pull_request` right after `branch_protection`); add three tests: `ok=None` child shows its error, `ok=None` parent shows its error, `ok=True` rows hide their error. |
