#!/usr/bin/env python3
"""
Manual integration test for multiple label detection.

This script tests that validate_labels.py correctly detects issues with
multiple workflow status labels.
"""

from pathlib import Path
from workflows.validate_labels import (
    check_status_labels,
    process_issues,
    build_label_lookups,
)
from workflows.label_config import load_labels_config


def test_multiple_labels_detection():
    """Test that check_status_labels correctly identifies multiple labels."""
    
    # Load real label configuration
    config_path = Path("workflows/config/labels.json")
    labels_config = load_labels_config(config_path)
    
    # Build label lookups
    label_lookups = build_label_lookups(labels_config)
    workflow_label_names = label_lookups["all_names"]
    
    print(f"Workflow labels: {sorted(workflow_label_names)}")
    print()
    
    # Test Case 1: Issue with no status labels
    issue_no_labels = {
        "number": 1,
        "labels": ["bug", "enhancement"],
        "title": "Test issue with no status labels"
    }
    
    count, status_labels = check_status_labels(issue_no_labels, workflow_label_names)
    print(f"Test Case 1 - No status labels:")
    print(f"  Issue #{issue_no_labels['number']}: {count} status labels")
    print(f"  Labels: {status_labels}")
    print(f"  Expected: count=0, labels=[]")
    print(f"  PASS: {count == 0 and status_labels == []}")
    print()
    
    # Test Case 2: Issue with exactly one status label
    issue_one_label = {
        "number": 2,
        "labels": ["status-01:created", "bug"],
        "title": "Test issue with one status label"
    }
    
    count, status_labels = check_status_labels(issue_one_label, workflow_label_names)
    print(f"Test Case 2 - One status label:")
    print(f"  Issue #{issue_one_label['number']}: {count} status labels")
    print(f"  Labels: {status_labels}")
    print(f"  Expected: count=1, labels=['status-01:created']")
    print(f"  PASS: {count == 1 and status_labels == ['status-01:created']}")
    print()
    
    # Test Case 3: Issue with multiple status labels (ERROR condition)
    issue_multiple_labels = {
        "number": 3,
        "labels": ["status-01:created", "status-03:planning", "bug"],
        "title": "Test issue with multiple status labels"
    }
    
    count, status_labels = check_status_labels(issue_multiple_labels, workflow_label_names)
    print(f"Test Case 3 - Multiple status labels (ERROR):")
    print(f"  Issue #{issue_multiple_labels['number']}: {count} status labels")
    print(f"  Labels: {status_labels}")
    print(f"  Expected: count=2, labels contain both 'status-01:created' and 'status-03:planning'")
    print(f"  PASS: {count == 2 and 'status-01:created' in status_labels and 'status-03:planning' in status_labels}")
    print()
    
    # Test Case 4: Issue with three status labels (ERROR condition)
    issue_three_labels = {
        "number": 4,
        "labels": [
            "status-01:created",
            "status-04:plan-review",
            "status-06:implementing",
            "enhancement"
        ],
        "title": "Test issue with three status labels"
    }
    
    count, status_labels = check_status_labels(issue_three_labels, workflow_label_names)
    print(f"Test Case 4 - Three status labels (ERROR):")
    print(f"  Issue #{issue_three_labels['number']}: {count} status labels")
    print(f"  Labels: {status_labels}")
    print(f"  Expected: count=3")
    print(f"  PASS: {count == 3}")
    print()
    
    print("=" * 60)
    print("All test cases completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_multiple_labels_detection()
