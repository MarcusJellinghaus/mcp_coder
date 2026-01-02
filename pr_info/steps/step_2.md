# Step 2: Update `_find_implementation_section()` to Handle Phase Headers

## Summary Reference
See [summary.md](summary.md) for overall context and design decisions.

## Objective
Modify the `_find_implementation_section()` function to recognize phase headers as continuations within the Tasks section, rather than treating them as section boundaries.

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

## HOW: Code Changes

### Current Logic (Lines ~70-95 in task_tracker.py)

```python
elif in_impl_section:
    # Stop parsing when we hit Pull Request section
    if "pull request" in header_text:
        break
    # Stop parsing if we hit a same-level or higher-level section
    elif header_level <= impl_section_level:
        break
    # Otherwise, this is a subsection within our implementation section
    # Continue collecting it
```

### New Logic (Replace the above)

```python
elif in_impl_section:
    # Stop parsing when we hit Pull Request section
    if "pull request" in header_text:
        break
    # Check if this is a phase header (continuation of tasks section)
    elif header_level <= impl_section_level:
        # Phase headers are continuations, not section boundaries
        if "phase" in header_text:
            # Continue collecting phase content
            pass
        else:
            # Other same-level headers end the section
            break
    # Otherwise, this is a subsection within our implementation section
    # Continue collecting it
```

---

## ALGORITHM: Pseudocode (5 lines)

```
1. IF "pull request" in header → STOP (explicit end marker)
2. IF header_level <= section_level:
3.     IF "phase" in header → CONTINUE (phase is continuation)
4.     ELSE → STOP (unrelated section)
5. ELSE → CONTINUE (subsection like ### Step N)
```

---

## DATA: No Changes to Return Values

| Function | Return Type | Change |
|----------|-------------|--------|
| `_find_implementation_section()` | `str` | No change - just includes more content |

---

## Implementation Details

### Full Updated Function

Replace the `_find_implementation_section` function in `src/mcp_coder/workflow_utils/task_tracker.py`:

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
    lines = content.split("\n")
    in_impl_section = False
    impl_section_level = 0  # Track the header level of the implementation section
    impl_lines = []

    for line in lines:
        # Check for section headers (## or ###)
        if line.strip().startswith(("##", "###")):
            # Count the number of # characters to determine header level
            header_level = len(line.strip()) - len(line.strip().lstrip("#"))
            header_text = line.strip().lstrip("#").strip().lower()

            # Look for either "implementation steps" or "tasks" sections
            if "implementation steps" in header_text or header_text == "tasks":
                in_impl_section = True
                impl_section_level = header_level
                continue
            elif in_impl_section:
                # Stop parsing when we hit Pull Request section
                if "pull request" in header_text:
                    break
                # Check if this is a phase header (continuation of tasks section)
                elif header_level <= impl_section_level:
                    # Phase headers are continuations, not section boundaries
                    if "phase" in header_text:
                        # Continue collecting phase content
                        pass
                    else:
                        # Other same-level headers end the section
                        break
                # Otherwise, this is a subsection within our implementation section
                # Continue collecting it

        # Collect lines if we're in the implementation section
        if in_impl_section:
            impl_lines.append(line)

    if not in_impl_section:
        raise TaskTrackerSectionNotFoundError(
            "Implementation Steps or Tasks section not found in TASK_TRACKER.md"
        )

    return "\n".join(impl_lines)
```

---

## Edge Cases Handled

| Scenario | Header | Behavior |
|----------|--------|----------|
| Phase continuation | `## Phase 2: Fixes` | Continue parsing |
| Pull Request section | `## Pull Request` | Stop parsing |
| Progress Summary | `## Progress Summary` | Stop parsing (not "phase") |
| Subsection | `### Step 3: Details` | Continue parsing (lower level) |

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
- See pr_info/steps/step_2.md for this step's details
- Step 1 added failing tests - now we implement the fix

TASK:
1. Open src/mcp_coder/workflow_utils/task_tracker.py
2. Find the _find_implementation_section() function
3. Update the header parsing logic to recognize "phase" headers as continuations
4. The key change is: when header_level <= impl_section_level, check if "phase" in header_text

REQUIREMENTS:
- Minimal code change - only modify the elif block inside the header parsing loop
- Maintain backward compatibility - existing tests must still pass
- Follow existing code style

KEY CODE CHANGE:
Replace:
    elif header_level <= impl_section_level:
        break

With:
    elif header_level <= impl_section_level:
        if "phase" in header_text:
            pass  # Phase headers are continuations
        else:
            break  # Other same-level headers end section

FILES TO MODIFY:
- src/mcp_coder/workflow_utils/task_tracker.py
```
