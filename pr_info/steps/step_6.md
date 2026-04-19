# Step 6: GitHub Action generation (`--generate-github-actions`)

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 6: Add GitHub Action workflow generation to `define_labels.py`. When `--generate-github-actions` is set, write `label-new-issues.yml` and `approve-command.yml` to `{project_dir}/.github/workflows/`. Write tests first (TDD), then implement. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/cli/commands/define_labels.py` — add generation functions
- `tests/cli/commands/test_define_labels.py` — add generation tests

## WHAT

### New functions in `define_labels.py`

```python
def generate_label_new_issues_yml(default_label_name: str) -> str:
    """Return the YAML content for label-new-issues.yml.
    
    Args:
        default_label_name: The label name from the default: true entry.
    
    Returns:
        Complete YAML file content as string.
    """
```

```python
def generate_approve_command_yml(
    promotions: list[tuple[str, str]],
) -> str:
    """Return the YAML content for approve-command.yml.
    
    Args:
        promotions: List of (current_label, next_label) tuples
                   derived from promotable: true labels.
    
    Returns:
        Complete YAML file content as string.
    """
```

```python
def build_promotions(labels_config: Dict[str, Any]) -> list[tuple[str, str]]:
    """Build promotion paths from promotable labels.
    
    For each label with promotable: true, the promotion target
    is the next label in the workflow_labels list.
    
    Args:
        labels_config: Loaded labels config.
    
    Returns:
        List of (source_label_name, target_label_name) tuples.
    """
```

```python
def write_github_actions(
    project_dir: Path,
    labels_config: Dict[str, Any],
    dry_run: bool = False,
) -> list[str]:
    """Write GitHub Action workflow files.
    
    Args:
        project_dir: Project root directory.
        labels_config: Loaded labels config.
        dry_run: If True, log what would be written without writing.
    
    Returns:
        List of file paths that were (or would be) written.
    """
```

## HOW

- `generate_label_new_issues_yml` and `generate_approve_command_yml` return f-strings with the YAML content
- `build_promotions` iterates `workflow_labels`, finds `promotable: true` entries, pairs with next entry
- `write_github_actions` creates `.github/workflows/` dir, writes files, logs warnings if overwriting
- Called from `execute_define_labels` when `generate_github_actions` flag is set
- With `--dry-run`, logs file paths that would be written but does not write

## ALGORITHM

### `build_promotions`:
```python
promotions = []
labels = config["workflow_labels"]
for i, label in enumerate(labels):
    if label.get("promotable") and i + 1 < len(labels):
        promotions.append((label["name"], labels[i + 1]["name"]))
return promotions
```

### `write_github_actions`:
```python
default_label = next(l["name"] for l in config["workflow_labels"] if l.get("default"))
promotions = build_promotions(config)
workflows_dir = project_dir / ".github" / "workflows"

files_to_write = {
    workflows_dir / "label-new-issues.yml": generate_label_new_issues_yml(default_label),
    workflows_dir / "approve-command.yml": generate_approve_command_yml(promotions),
}

if dry_run:
    for path in files_to_write: logger.info(f"Would write: {path}")
    return [str(p) for p in files_to_write]

workflows_dir.mkdir(parents=True, exist_ok=True)
for path, content in files_to_write.items():
    if path.exists(): logger.warning(f"Overwriting: {path}")
    path.write_text(content)
return [str(p) for p in files_to_write]
```

## DATA

- `generate_label_new_issues_yml("status-01:created")` returns YAML string with that label name
- `generate_approve_command_yml([("status-01:created", "status-02:awaiting-planning"), ...])` returns YAML with promotion map
- `build_promotions(config)` returns `[("status-01:created", "status-02:awaiting-planning"), ("status-04:plan-review", "status-05:plan-ready"), ("status-07:code-review", "status-08:ready-pr")]`

## Tests (TDD — write first)

```python
class TestBuildPromotions:
    def test_builds_from_promotable_labels(self):
        """Extracts (current, next) pairs from promotable: true labels."""
        
    def test_empty_when_no_promotable(self):
        """Returns empty list when no labels are promotable."""

class TestGenerateLabelNewIssuesYml:
    def test_contains_default_label(self):
        """Generated YAML references the default label name."""
        
    def test_valid_yaml_structure(self):
        """Generated content is valid YAML with expected structure."""

class TestGenerateApproveCommandYml:
    def test_contains_promotion_paths(self):
        """Generated YAML includes all promotion source/target pairs."""
        
    def test_valid_yaml_structure(self):
        """Generated content is valid YAML with expected structure."""

class TestWriteGithubActions:
    def test_writes_two_files(self, tmp_path):
        """Writes label-new-issues.yml and approve-command.yml."""
        
    def test_dry_run_does_not_write(self, tmp_path):
        """With dry_run=True, no files are created."""
        
    def test_overwrites_existing_with_warning(self, tmp_path, caplog):
        """Existing files are overwritten with a warning logged."""
        
    def test_creates_workflows_directory(self, tmp_path):
        """Creates .github/workflows/ if it doesn't exist."""
```

## Verification

- All new and existing tests pass
- Generated YAML matches expected structure
- Pylint, mypy, pytest all green
