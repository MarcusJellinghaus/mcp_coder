# Step 3: CLI utils — add `resolve_issue_interaction_flags()` shared helper

## References
- See `pr_info/steps/summary.md` for overall architecture and design changes

## WHERE
- `src/mcp_coder/cli/utils.py` — new function
- `tests/cli/test_utils.py` — new test class

## WHAT

### New function in `cli/utils.py`

```python
def resolve_issue_interaction_flags(
    args: argparse.Namespace, project_dir: Path
) -> tuple[bool, bool]:
    """Resolve update_issue_labels and post_issue_comments settings.

    Priority: CLI flag (if not None) > config.toml repo section > default (False).

    Looks up the local git remote URL, finds matching [coordinator.repos.*]
    section in config.toml, and merges with CLI flags.

    Args:
        args: Parsed CLI args with update_issue_labels and post_issue_comments
              (both bool | None from BooleanOptionalAction)
        project_dir: Project directory for git remote URL detection

    Returns:
        Tuple of (update_issue_labels: bool, post_issue_comments: bool)
    """
```

## HOW
- Import `get_github_repository_url` from `mcp_coder.utils.git_operations.remotes`
- Import `find_repo_section_by_url`, `get_config_values` from `mcp_coder.utils.user_config`
- Add `import argparse` at top
- Add to `__all__` list

## ALGORITHM (pseudocode)
```
def resolve_issue_interaction_flags(args, project_dir):
    cli_labels = getattr(args, "update_issue_labels", None)
    cli_comments = getattr(args, "post_issue_comments", None)
    
    # Get config values (default False)
    cfg_labels, cfg_comments = False, False
    repo_url = get_github_repository_url(project_dir)
    if repo_url:
        section = find_repo_section_by_url(repo_url)
        if section:
            config = get_config_values([(section, "update_issue_labels", None),
                                         (section, "post_issue_comments", None)])
            cfg_labels = config[(section, "update_issue_labels")] == "True"
            cfg_comments = config[(section, "post_issue_comments")] == "True"
    
    # Merge: CLI wins if not None, else config, else False
    return (cli_labels if cli_labels is not None else cfg_labels,
            cli_comments if cli_comments is not None else cfg_comments)
```

## DATA
- **Input:** `args.update_issue_labels: bool | None`, `args.post_issue_comments: bool | None`, `project_dir: Path`
- **Output:** `tuple[bool, bool]` — resolved `(update_issue_labels, post_issue_comments)`
- **Config values:** stored as TOML booleans (`true`/`false`), read via `get_config_values()` as strings `"True"`/`"False"`

## TESTS (TDD — write first)

New class `TestResolveIssueInteractionFlags` in `tests/cli/test_utils.py`:

1. **`test_defaults_to_false_false_when_no_cli_no_config`** — args have both `None`, no config match → `(False, False)`
2. **`test_cli_flags_override_config`** — config has both `true`, CLI has both `False` → `(False, False)`
3. **`test_config_values_used_when_cli_none`** — config has `update_issue_labels = true`, CLI is `None` → `(True, False)`
4. **`test_cli_true_overrides_config_false`** — config has both `false`, CLI has both `True` → `(True, True)`
5. **`test_no_git_remote_falls_back_to_defaults`** — `get_github_repository_url` returns `None` → `(False, False)`
6. **`test_no_matching_repo_section_falls_back_to_defaults`** — remote URL doesn't match any config section → `(False, False)`
7. **`test_partial_cli_override`** — CLI sets `update_issue_labels=True` but `post_issue_comments=None`, config has `post_issue_comments=true` → `(True, True)`

Tests mock `get_github_repository_url`, `find_repo_section_by_url`, and `get_config_values`.

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3: add resolve_issue_interaction_flags() to cli/utils.py.

1. Write tests FIRST in tests/cli/test_utils.py (new TestResolveIssueInteractionFlags class)
2. Implement resolve_issue_interaction_flags() in src/mcp_coder/cli/utils.py
3. Add necessary imports and update __all__
4. Run all code quality checks (pylint, pytest, mypy)
5. Fix any issues until all checks pass
```

## COMMIT MESSAGE
```
feat: add resolve_issue_interaction_flags helper (#661)

Shared CLI helper that resolves update_issue_labels and post_issue_comments
from CLI flags > config.toml repo section > default (False). Uses git
remote URL to find matching [coordinator.repos.*] config section.
```
