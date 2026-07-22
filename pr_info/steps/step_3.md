# Step 3 — Config flags (`auto_review_plan` / `auto_review_implementation`)

> References `pr_info/steps/summary.md` (Config flags). **Define + verify only**; consumption
> (gating the success transition) is #1073.

## WHERE
- `src/mcp_coder/utils/user_config.py` (modify — `_CONFIG_SCHEMA["coordinator.repos.*"]`, ~line 63)
- `tests/utils/test_user_config*.py` (modify — add assertions)

## WHAT
Add two boolean fields to the existing `coordinator.repos.*` wildcard section, mirroring
`update_issue_labels` / `post_issue_comments`:
```python
"coordinator.repos.*": {
    ...
    "update_issue_labels": FieldDef(bool),
    "post_issue_comments": FieldDef(bool),
    "auto_review_plan": FieldDef(bool),            # new, default false
    "auto_review_implementation": FieldDef(bool),  # new, default false
    ...
},
```

## HOW
- No new code path: `_get_field_def` already routes `coordinator.repos.<name>` keys through the
  `coordinator.repos.*` wildcard, and `_verify_wildcard_repos` → `_verify_section` type-checks
  every declared field and warns on unknown keys. Declaring the `FieldDef`s is sufficient for
  both parse and verify.
- "Default false" = absent key resolves to `False` at the (future) call site; no default is
  stored in the schema (matches the sibling bool flags).

## ALGORITHM
- None (declarative schema addition).

## DATA
- `FieldDef(bool)` entries; boolean values read via the existing typed getters.

## TDD / checks
- Test first: in `tests/utils/test_user_config*.py`, add a repo section with
  `auto_review_plan = true` / `auto_review_implementation = false` and assert the values parse
  as booleans and that verification reports **no** unknown-key warning for them; assert an
  invalid type (e.g. a string) is rejected/flagged like the sibling flags.
- Run: `run_pytest_check(extra_args=["-n","auto","-k","user_config"])`, then pylint + mypy.

## LLM prompt for this step
> Implement Step 3 of `pr_info/steps/summary.md`. First add failing tests in
> `tests/utils/test_user_config*.py` proving `auto_review_plan` and
> `auto_review_implementation` under a `coordinator.repos.<name>` section parse as booleans and
> verify cleanly (no unknown-key warning), and that a wrong type is flagged. Then add the two
> `FieldDef(bool)` entries to `_CONFIG_SCHEMA["coordinator.repos.*"]` in
> `src/mcp_coder/utils/user_config.py`, next to `update_issue_labels`/`post_issue_comments`. Do
> not add any consumption logic. Run the user_config tests, pylint, mypy.
