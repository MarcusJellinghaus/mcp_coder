# Summary: Make issue label updates and comment posting configurable per-repo (#661)

## Goal

Replace the single `--update-labels` CLI flag with two independent, granular configuration keys (`update_issue_labels`, `post_issue_comments`) that can be set per-repo in `config.toml` and overridden via CLI flags.

## Architectural / Design Changes

### Before
- Single `--update-labels` boolean flag (`store_true`) on `implement`, `create-plan`, `create-pr` CLI commands
- Coordinator templates hardcode `--update-labels` in Jenkins command strings
- `handle_workflow_failure()` always posts GitHub comments regardless of `update_labels` flag
- No per-repo configuration for issue interaction behavior
- Single `update_labels: bool` parameter flows through workflows → failure handling

### After
- Two `BooleanOptionalAction` CLI flags: `--update-issue-labels`/`--no-update-issue-labels` and `--post-issue-comments`/`--no-post-issue-comments` (three-state: True/False/None)
- Per-repo config keys in `[coordinator.repos.<name>]`: `update_issue_labels` and `post_issue_comments` (default: `false`)
- Override priority: CLI flag (if not None) > config.toml value > default (`false`)
- Coordinator templates no longer pass any flags — executors resolve settings from config via repo URL matching
- `handle_workflow_failure()` gates comment posting on `post_issue_comments` (no longer unconditional)
- New `find_repo_section_by_url()` helper matches local git remote URL to config section
- New `resolve_issue_interaction_flags()` shared helper in `cli/utils.py` centralizes the resolution logic (avoids duplication across 3 CLI commands)

### Data Flow (After)

```
CLI flags (None/True/False)
         │
         ▼
resolve_issue_interaction_flags()
  ├── get git remote URL
  ├── find_repo_section_by_url() → config section name
  ├── get_config_values() → config bools
  └── merge: CLI > config > default(false)
         │
         ▼
(update_issue_labels: bool, post_issue_comments: bool)
         │
         ▼
workflow function (implement/create-pr/create-plan)
         │
         ▼
handle_workflow_failure(update_issue_labels=..., post_issue_comments=...)
```

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/utils/user_config.py` | Add `find_repo_section_by_url()`, update default config template |
| `src/mcp_coder/cli/parsers.py` | Replace `--update-labels` with two `BooleanOptionalAction` flags |
| `src/mcp_coder/cli/utils.py` | Add `resolve_issue_interaction_flags()` shared helper |
| `src/mcp_coder/cli/commands/implement.py` | Use shared helper, pass two bools to workflow |
| `src/mcp_coder/cli/commands/create_pr.py` | Use shared helper, pass two bools to workflow |
| `src/mcp_coder/cli/commands/create_plan.py` | Use shared helper, pass two bools to workflow |
| `src/mcp_coder/cli/commands/coordinator/core.py` | Extend `load_repo_config()` with 2 extra keys |
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Remove `--update-labels` from all 6 templates |
| `src/mcp_coder/workflow_utils/failure_handling.py` | Rename `update_labels` → `update_issue_labels`, add `post_issue_comments`, gate comments |
| `src/mcp_coder/workflows/create_pr/helpers.py` | Rename `update_labels` → `update_issue_labels`, add `post_issue_comments` |
| `src/mcp_coder/workflows/implement/core.py` | Rename param, add param, pass both downstream |
| `src/mcp_coder/workflows/create_pr/core.py` | Rename param, add param, pass both downstream |
| `src/mcp_coder/workflows/create_plan.py` | Rename param, add param |
| `docs/configuration/config.md` | Document new per-repo settings |
| `docs/cli-reference.md` | Update CLI flag documentation |

## Files with Test Changes

| Test File | Tests For |
|-----------|-----------|
| `tests/utils/test_user_config.py` | `find_repo_section_by_url()` |
| `tests/cli/test_parsers.py` | New `BooleanOptionalAction` flags |
| `tests/cli/test_utils.py` | `resolve_issue_interaction_flags()` |
| `tests/cli/commands/test_implement.py` | Updated parameter passing |
| `tests/cli/commands/test_create_pr.py` | Updated parameter passing |
| `tests/cli/commands/test_create_plan.py` | Updated parameter passing |
| `tests/cli/commands/coordinator/test_core.py` | Extended `load_repo_config()` |
| `tests/workflow_utils/test_failure_handling.py` | Split flags, comment gating |
| `tests/workflows/create_pr/test_failure_handling.py` | Updated helpers |
| `tests/workflows/implement/test_core.py` | Updated workflow params |
| `tests/workflows/create_pr/test_workflow.py` | Updated workflow params |
| `tests/workflows/create_plan/test_main.py` | Updated workflow params |

## Implementation Steps

| Step | Description | Commit |
|------|-------------|--------|
| 1 | `find_repo_section_by_url()` in user_config.py + tests | Config layer: add find_repo_section_by_url |
| 2 | CLI parsers: replace `--update-labels` with two `BooleanOptionalAction` flags + tests | CLI: replace --update-labels with granular flags |
| 3 | `resolve_issue_interaction_flags()` in cli/utils.py + tests | CLI: add resolve_issue_interaction_flags helper |
| 4 | `failure_handling.py`: rename + add `post_issue_comments` gating + tests | Failure handling: split into two flags |
| 5 | `create_pr/helpers.py`: rename + add param + tests | Create-pr helpers: update failure params |
| 6 | Workflow cores: rename params + pass both flags + update CLI commands + tests | Workflows + CLI commands: wire up both flags |
| 7 | Coordinator: extend `load_repo_config()` + remove `--update-labels` from templates + tests | Coordinator: config keys + remove template flags |
| 8 | Default config template + documentation | Docs: update config template and references |
