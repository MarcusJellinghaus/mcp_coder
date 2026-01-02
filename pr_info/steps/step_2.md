# Step 2: Simplify `_find_implementation_section()` with Boundary-Based Extraction

## Summary Reference
See [summary.md](summary.md) for overall context and design decisions.
See [Decisions.md](Decisions.md) for decisions made during plan review.

## Objective
Replace the complex header-level tracking logic with a simpler boundary-based extraction approach. This finds everything between `## Tasks` and `## Pull Request` markers.

**Why this change?** The original approach tracked header levels and used keyword detection. The new approach is simpler, more robust, and handles any structure within the Tasks section (phases, sprints, parts, etc.) without needing keyword lists.

---

## WHERE: File Paths

| Action | File Path |
|--------|-----------|
| Modify | `src/mcp_coder/workflow_utils/task_tracker.py` |

---

## WHAT: Function to Modify

### Function Signature (unchanged)
```python
def _find_implementation_section(content: str) -> str:
    """Find and extract Implementation Steps or Tasks section, raise exception if missing.

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        Content of Implementation Steps or Tasks section (without header)

    Raises:
        TaskTrackerSectionNotFoundError: If Implementation Steps or Tasks section not found
    """
```

---

## HOW: Approach Change

### Current Approach (complex)
- Track header levels
- Compare levels to determine section boundaries  
- Stop at same-level or higher-level headers
- Problem: `## Phase 2:` is same level as `## Tasks`, stops too early

### New Approach (boundary-based)
- Find start marker: `## Tasks` or `### Implementation Steps`
- Find end marker: `## Pull Request` (case-insensitive)
- Extract everything between them
- If no end marker, extract to end of file
- Add debug logging for troubleshooting

---

## ALGORITHM: Pseudocode

```
1. Scan lines for start marker ("## tasks" or "### implementation steps")
2. Record start line number and header text
3. Continue scanning for end marker ("## pull request")
4. Record end line number (or use last line if no end marker)
5. Extract lines between start and end
6. Log debug info: start header, end header, line numbers, count
7. Return extracted content
```

---

## DATA: No Changes to Return Values

| Function | Return Type | Change |
|----------|-------------|--------|
| `_find_implementation_section()` | `str` | No change - just includes more content |

---

## Implementation Details

### New Requirement: Add Module-Level Logging

The `task_tracker.py` module currently has no logging. Add the standard logging pattern used throughout this codebase:

```python
import logging

logger = logging.getLogger(__name__)
```

Add these lines near the top of the file, after the existing imports (after `from pathlib import Path`). This follows the project's established pattern (see `claude_code_api.py`, `core.py` for examples) and enables debug-level troubleshooting for section extraction.

### Full Updated Function

Replace the `_find_implementation_section` function in `src/mcp_coder/workflow_utils/task_tracker.py`:

```python
def _find_implementation_section(content: str) -> str:
    """Find and extract Implementation Steps or Tasks section, raise exception if missing.

    Uses boundary-based extraction: finds content between the Tasks/Implementation Steps
    header and the Pull Request header (or end of file if no Pull Request section).

    Args:
        content: Full TASK_TRACKER.md content

    Returns:
        Content of Implementation Steps or Tasks section (without header)

    Raises:
        TaskTrackerSectionNotFoundError: If Implementation Steps or Tasks section not found
    """
    lines = content.split("\n")
    start_line: int | None = None
    start_header: str | None = None
    end_line: int | None = None
    end_header: str = "end of file"

    for i, line in enumerate(lines):
        # Check for section headers (## or ###)
        if line.strip().startswith(("#")):
            header_text = line.strip().lstrip("#").strip().lower()

            # Look for start marker: "implementation steps" or "tasks"
            if start_line is None:
                if "implementation steps" in header_text or header_text == "tasks":
                    start_line = i + 1  # Start after the header line
                    start_header = line.strip()
            else:
                # Look for end marker: "pull request"
                if "pull request" in header_text:
                    end_line = i
                    end_header = line.strip()
                    break

    # Check if we found the start marker
    if start_line is None or start_header is None:
        raise TaskTrackerSectionNotFoundError(
            "Implementation Steps or Tasks section not found in TASK_TRACKER.md"
        )

    # If no end marker found, use end of file
    if end_line is None:
        end_line = len(lines)

    # Extract lines between boundaries
    impl_lines = lines[start_line:end_line]
    line_count = len(impl_lines)

    logger.debug(
        "Found Tasks section between '%s' and '%s', lines %d to %d (%d lines)",
        start_header,
        end_header,
        start_line + 1,  # 1-based for human readability
        end_line,
        line_count,
    )

    return "\n".join(impl_lines)
```

**Note:** Add the `import logging` and `logger = logging.getLogger(__name__)` at the top of the file if not already present.

---

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| `## Phase 2: Fixes` within Tasks | Included (between boundaries) |
| `## Sprint 3: Cleanup` within Tasks | Included (between boundaries) |
| `## Pull Request` | Marks end boundary, content excluded |
| `## PULL REQUEST` (uppercase) | Marks end boundary (case-insensitive) |
| No Pull Request section | Extract to end of file |
| `### Step 3: Details` | Included (between boundaries) |

---

## Verification

After implementing the fix, run:
```bash
pytest tests/workflow_utils/test_task_tracker.py -v
```

**Expected Result**: All tests should **PASS**, including the new multi-phase tests from Step 1.

---

## LLM Prompt for Step 2

```
You are implementing Step 2 of issue #156: Support for Multi-Phase Task Tracker.

CONTEXT:
- See pr_info/steps/summary.md for overall design
- See pr_info/steps/Decisions.md for design decisions
- See pr_info/steps/step_2.md for this step's details
- Step 1 added failing tests - now we implement the fix

TASK:
1. Open src/mcp_coder/workflow_utils/task_tracker.py
2. Add logging import and logger at module level if not present
3. Replace the entire _find_implementation_section() function with the new boundary-based version
4. The new approach: find content between "## Tasks" and "## Pull Request" markers

REQUIREMENTS:
- Replace the entire function (cleaner than patching)
- Add debug logging for troubleshooting
- Maintain backward compatibility - existing tests must still pass
- Follow existing code style

FILES TO MODIFY:
- src/mcp_coder/workflow_utils/task_tracker.py
```
