# Step 7: Default config template + documentation

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/utils/user_config.py` — update `create_default_config()` template string
- `docs/configuration/config.md` — document new per-repo settings
- `docs/cli-reference.md` — update CLI flag documentation
- `tests/utils/test_user_config.py` — update existing template content test

## WHAT

### Update default config template in `create_default_config()`

Add `update_issue_labels` and `post_issue_comments` keys to the example repo sections:

```toml
[coordinator.repos.mcp_coder]
repo_url = "https://github.com/your-org/mcp_coder.git"
executor_job_path = "Tests/mcp-coder-coordinator-test"
github_credentials_id = "github-general-pat"
executor_os = "linux"
update_issue_labels = true
post_issue_comments = true
```

Same for `mcp_workspace` section and the commented-out example.

### Update `docs/configuration/config.md`

In the `[coordinator.repos.*]` section table, add:

| Field | Type | Description | Required | Default |
|-------|------|-------------|----------|---------|
| `update_issue_labels` | boolean | Update GitHub issue labels on workflow success/failure | No | `false` |
| `post_issue_comments` | boolean | Post GitHub comments on workflow failure | No | `false` |

Add example showing per-repo configuration.

### Update `docs/cli-reference.md`

For `implement`, `create-plan`, `create-pr` commands:

**Remove:**
- `--update-labels` — Automatically update GitHub issue labels on successful completion

**Add:**
- `--update-issue-labels` / `--no-update-issue-labels` — Update GitHub issue labels on success/failure (default: from config.toml, or false)
- `--post-issue-comments` / `--no-post-issue-comments` — Post GitHub comments on workflow failure (default: from config.toml, or false)

Update the "Common Patterns" section example:
```bash
# 2. Execute implementation (with explicit flags)
mcp-coder implement --update-issue-labels --post-issue-comments
```

## HOW
- Template string edit in `create_default_config()`
- Markdown edits in docs files
- No code logic changes

## ALGORITHM
No algorithm — documentation and template changes only.

## DATA
No data changes.

## TESTS

### Update `tests/utils/test_user_config.py`:

1. **`test_create_default_config_content_has_all_sections`** — assert `update_issue_labels` and `post_issue_comments` keys exist in the parsed TOML for repo sections
2. **`test_create_default_config_content_has_example_repos`** — assert example repos include the new keys

These are updates to existing tests (not new tests).

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_7.md.

Implement Step 7: update default config template and documentation.

1. Update tests FIRST in tests/utils/test_user_config.py:
   - Update test_create_default_config_content_has_all_sections to verify new keys
   - Update test_create_default_config_content_has_example_repos to verify new keys

2. Update source:
   - src/mcp_coder/utils/user_config.py — add new keys to create_default_config() template

3. Update documentation:
   - docs/configuration/config.md — add new fields to [coordinator.repos.*] table and examples
   - docs/cli-reference.md — replace --update-labels with new flags in implement, create-plan, create-pr sections

4. Run all code quality checks (pylint, pytest, mypy)
5. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
docs: document update_issue_labels and post_issue_comments settings (#661)

Update default config template with new per-repo settings.
Document new [coordinator.repos.*] fields in config.md.
Update CLI reference with new --update-issue-labels and
--post-issue-comments flags replacing --update-labels.
```
