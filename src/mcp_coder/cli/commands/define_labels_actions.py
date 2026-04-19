"""GitHub Action workflow file generation for define-labels.

This module handles generating and writing GitHub Action workflow files
(label-new-issues.yml and approve-command.yml) based on labels config.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_label_new_issues_yml(default_label_name: str) -> str:
    """Return the YAML content for label-new-issues.yml.

    Args:
        default_label_name: The label name from the default: true entry.

    Returns:
        Complete YAML file content as string.
    """
    return f"""name: Label New Issues

on:
  issues:
    types: [opened]

jobs:
  add-label:
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Add status label
        uses: actions/github-script@v8
        with:
          script: |
            github.rest.issues.addLabels({{
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: ['{default_label_name}']
            }});
"""


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
    # Build the promotions object for the JavaScript
    promotion_lines = []
    for current, target in promotions:
        promotion_lines.append(f"              '{current}': '{target}',")
    promotions_block = "\n".join(promotion_lines)

    # Build the status list for the error message
    status_list = "\n".join(f"- \\`{current}\\`" for current, _ in promotions)

    return f"""name: Approve Command

on:
  issue_comment:
    types: [created]

jobs:
  handle-approve:
    runs-on: ubuntu-latest
    # Only run on issues (not PRs) and when comment is /approve
    if: github.event.issue.pull_request == null && contains(github.event.comment.body, '/approve')
    permissions:
      issues: write
    steps:
      - name: Handle approve command
        uses: actions/github-script@v8
        with:
          script: |
            const comment = context.payload.comment.body.trim();

            // Only process if comment is exactly /approve
            if (comment !== '/approve') {{
              return;
            }}

            const issue = context.payload.issue;
            const labels = issue.labels.map(l => l.name);

            // Define the promotion paths: [current_status, next_status]
            const promotions = {{
{promotions_block}
            }};

            let promoted = false;
            let oldStatus = null;
            let newStatus = null;

            // Check which status the issue currently has and promote it
            for (const [currentStatus, nextStatus] of Object.entries(promotions)) {{
              if (labels.includes(currentStatus)) {{
                // Remove old status
                await github.rest.issues.removeLabel({{
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  name: currentStatus
                }}).catch(() => {{}}); // Ignore errors if label doesn't exist

                // Add new status
                await github.rest.issues.addLabels({{
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  labels: [nextStatus]
                }});

                oldStatus = currentStatus;
                newStatus = nextStatus;
                promoted = true;
                break;
              }}
            }}

            // Post confirmation comment
            if (promoted) {{
              await github.rest.issues.createComment({{
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `✅ Status promoted: \\\\`${{oldStatus}}\\\\` → \\\\`${{newStatus}}\\\\`\\\\n\\\\nThe bot can now pick up this issue for the next step.`
              }});
            }} else {{
              // No matching status found
              await github.rest.issues.createComment({{
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `⚠️ Cannot promote issue. The issue must have one of these statuses:\\\\n{status_list}\\\\n\\\\nCurrent labels: ${{labels.filter(l => l.startsWith('status-')).join(', ') || 'none'}}`
              }});
            }}
"""


def build_promotions(labels_config: dict[str, Any]) -> list[tuple[str, str]]:
    """Build promotion paths from promotable labels.

    For each label with promotable: true, the promotion target
    is the next label in the workflow_labels list.

    Args:
        labels_config: Loaded labels config.

    Returns:
        List of (source_label_name, target_label_name) tuples.
    """
    promotions: list[tuple[str, str]] = []
    labels = labels_config["workflow_labels"]
    for i, label in enumerate(labels):
        if label.get("promotable") and i + 1 < len(labels):
            promotions.append((label["name"], labels[i + 1]["name"]))
    return promotions


def write_github_actions(
    project_dir: Path,
    labels_config: dict[str, Any],
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
    default_label = next(
        label["name"]
        for label in labels_config["workflow_labels"]
        if label.get("default")
    )
    promotions = build_promotions(labels_config)
    workflows_dir = project_dir / ".github" / "workflows"

    files_to_write = {
        workflows_dir
        / "label-new-issues.yml": generate_label_new_issues_yml(default_label),
        workflows_dir / "approve-command.yml": generate_approve_command_yml(promotions),
    }

    if dry_run:
        for path in files_to_write:
            logger.info("Would write: %s", path)
        return [str(p) for p in files_to_write]

    workflows_dir.mkdir(parents=True, exist_ok=True)
    for path, content in files_to_write.items():
        if path.exists():
            logger.warning("Overwriting: %s", path)
        path.write_text(content, encoding="utf-8")
    return [str(p) for p in files_to_write]
