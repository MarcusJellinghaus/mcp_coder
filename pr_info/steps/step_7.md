# Step 7: Coordinator — extend config + remove template flags

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/cli/commands/coordinator/core.py` — extend `load_repo_config()`
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — remove `--update-labels` from templates
- `tests/cli/commands/coordinator/test_core.py` — update tests
- Tests for command templates (if any exist, or add assertions)

## WHAT

### Changes to `load_repo_config()` in `core.py`

Add two extra keys to the `get_config_values()` batch call:

```python
config = get_config_values(
    [
        (section, "repo_url", None),
        (section, "executor_job_path", None),
        (section, "github_credentials_id", None),
        (section, "executor_os", None),
        (section, "update_issue_labels", None),      # NEW
        (section, "post_issue_comments", None),       # NEW
    ]
)
```

Add to return dict:
```python
return {
    "repo_url": repo_url,
    "executor_job_path": executor_job_path,
    "github_credentials_id": github_credentials_id,
    "executor_os": executor_os,
    "update_issue_labels": config[(section, "update_issue_labels")] == "True",
    "post_issue_comments": config[(section, "post_issue_comments")] == "True",
}
```

Note: `get_config_values()` returns strings (TOML booleans become `"True"`/`"False"`). Compare with `== "True"` to get bool. Missing values return `None` which is `!= "True"` → `False` (correct default).

**Return type:** The current annotation `dict[str, Optional[str]]` must be updated to `dict[str, str | bool | None]` since the new keys return `bool` values.

### Changes to `command_templates.py`

Remove `--update-labels` from all 6 command template strings:

- `CREATE_PLAN_COMMAND_TEMPLATE` — remove `--update-labels`
- `IMPLEMENT_COMMAND_TEMPLATE` — remove `--update-labels`
- `CREATE_PR_COMMAND_TEMPLATE` — remove `--update-labels`
- `CREATE_PLAN_COMMAND_WINDOWS` — remove `--update-labels`
- `IMPLEMENT_COMMAND_WINDOWS` — remove `--update-labels`
- `CREATE_PR_COMMAND_WINDOWS` — remove `--update-labels`

## HOW
- No new imports needed in core.py
- Template changes are pure string edits (remove ` --update-labels` from each mcp-coder command line)

## ALGORITHM
No algorithm — config extension and string removal.

## DATA
- `load_repo_config()` return type gains two bool keys: `update_issue_labels` and `post_issue_comments`
- Both default to `False` when not present in config

## TESTS

### Update `tests/cli/commands/coordinator/test_core.py`:

1. **`test_load_repo_config_includes_issue_interaction_flags`** — config has both `true` → returned dict has `update_issue_labels=True, post_issue_comments=True`
2. **`test_load_repo_config_defaults_flags_when_missing`** — config has no flags → `update_issue_labels=False, post_issue_comments=False`

### Template tests (assertions in existing or new test file):

3. **`test_templates_do_not_contain_update_labels_flag`** — assert `--update-labels` not in any of the 6 template strings

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_7.md.

Implement Step 7: extend coordinator config and clean up templates.

1. Write/update tests FIRST:
   - tests/cli/commands/coordinator/test_core.py — test load_repo_config returns new flags
   - Add test asserting --update-labels is absent from all templates

2. Modify source files:
   - src/mcp_coder/cli/commands/coordinator/core.py — extend load_repo_config() with 2 new keys
   - src/mcp_coder/cli/commands/coordinator/command_templates.py — remove --update-labels from all 6 templates

3. Run all code quality checks (pylint, pytest, mypy)
4. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: coordinator config keys + remove --update-labels from templates (#661)

Extend load_repo_config() to include update_issue_labels and
post_issue_comments (default False). Remove --update-labels flag
from all 6 Jenkins command templates — executors now resolve
settings from config.toml via repo URL matching.
```
