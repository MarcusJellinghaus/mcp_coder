"""Workflow configuration constants for coordinator operations.

This module defines the workflow state machine configuration:
- WorkflowConfig: TypedDict describing workflow execution parameters
- WORKFLOW_MAPPING: Maps status labels to workflow configurations

The workflow mapping connects GitHub issue status labels to:
- The workflow type to execute (create-plan, implement, create-pr)
- The branch strategy (main for planning, from_issue for implementation)
- The next status label to apply after dispatch

Label names must match those defined in config/labels.json.
Uses GitHub API label names directly (not internal_ids) for simpler code.
"""

from typing import TypedDict

from ....constants import DUPLICATE_PROTECTION_SECONDS


class WorkflowConfig(TypedDict):
    """Configuration for a single workflow stage.

    Attributes:
        workflow: Workflow type to execute ("create-plan", "implement", "create-pr")
        branch_strategy: How to determine branch ("main" or "from_issue")
        next_label: Status label to apply after successful dispatch
    """

    workflow: str
    branch_strategy: str
    next_label: str


# Re-export DUPLICATE_PROTECTION_SECONDS for backwards compatibility
__all__ = ["WorkflowConfig", "WORKFLOW_MAPPING", "DUPLICATE_PROTECTION_SECONDS"]

# Workflow configuration mapping
# IMPORTANT: Label names must match those defined in config/labels.json
# Uses GitHub API label names directly (not internal_ids) for simpler code
WORKFLOW_MAPPING: dict[str, WorkflowConfig] = {
    "status-02:awaiting-planning": {
        "workflow": "create-plan",
        "branch_strategy": "main",
        "next_label": "status-03:planning",
    },
    "status-05:plan-ready": {
        "workflow": "implement",
        "branch_strategy": "from_issue",
        "next_label": "status-06:implementing",
    },
    "status-08:ready-pr": {
        "workflow": "create-pr",
        "branch_strategy": "from_issue",
        "next_label": "status-09:pr-creating",
    },
}
