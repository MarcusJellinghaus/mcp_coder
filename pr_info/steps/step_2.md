# Step 2: Update Workspace Functions and Gitignore

## LLM Prompt

```
Implement Step 2 of Issue #399 (see pr_info/steps/summary.md for context).

Update workspace.py functions and project .gitignore:
1. Update create_status_file() to write .txt file with simplified parameters
2. Update update_gitignore() idempotency check from .md to .txt
3. Add .vscodeclaude_status.txt to project root .gitignore

Follow TDD: update tests first, then implement.
```

## WHERE

**Files:**
- `src/mcp_coder/workflows/vscodeclaude/workspace.py`
  - `create_status_file()` (lines 313-351)
  - `update_gitignore()` (lines 238-252)
- `.gitignore` (project root)

## WHAT

### 1. create_status_file()

**Current signature:**
```python
def create_status_file(
    folder_path: Path,
    issue_number: int,
    issue_title: str,
    status: str,
    repo_full_name: str,
    branch_name: str,      # No longer used
    issue_url: str,
    is_intervention: bool,
) -> None:
```

**Keep same signature** - all parameters are used in the new format.

**Output:** `.vscodeclaude_status.txt` instead of `.vscodeclaude_status.md`

### 2. update_gitignore()

**Change idempotency check:**
- Current: `if ".vscodeclaude_status.md" in existing_content`
- New: `if ".vscodeclaude_status.txt" in existing_content`

### 3. Project .gitignore

**Replace:** `.vscodeclaude_status.md` with `.vscodeclaude_status.txt`

## HOW

### create_status_file() changes:
- Import only `STATUS_FILE_TEMPLATE` (remove `INTERVENTION_ROW` import)
- Build `intervention_line` string conditionally
- Change output filename from `.md` to `.txt`
- Simplify template format call

### update_gitignore() changes:
- Single string replacement in idempotency check

## ALGORITHM

```python
# create_status_file() pseudocode
def create_status_file(...):
    config = get_vscodeclaude_config(status)
    status_emoji = config["emoji"] if config else "📋"
    
    # Build intervention line (empty or "Mode:    ⚠️ INTERVENTION\n")
    intervention_line = "Mode:    ⚠️ INTERVENTION\n" if is_intervention else ""
    
    content = STATUS_FILE_TEMPLATE.format(
        status_emoji=status_emoji,
        issue_number=issue_number,
        title=issue_title,
        repo=repo_full_name,
        status_name=status,
        branch=branch_name,
        started_at=datetime.now(timezone.utc).isoformat(),
        intervention_line=intervention_line,
        issue_url=issue_url,
    )
    
    status_file = folder_path / ".vscodeclaude_status.txt"  # Changed extension
    status_file.write_text(content, encoding="utf-8")
```

```python
# update_gitignore() pseudocode
def update_gitignore(folder_path: Path) -> None:
    # ... read existing content ...
    
    # Check if already present (changed from .md to .txt)
    if ".vscodeclaude_status.txt" in existing_content:
        return
    
    # ... append entry ...
```

## DATA

### Input (unchanged)
All function parameters remain the same.

### Output
- `create_status_file()`: Creates `.vscodeclaude_status.txt` with plain text content
- `update_gitignore()`: Appends gitignore entry (now with `.txt`)

### Example status file content
```
==========================================================================
📝 Issue #399 - vscodeclaude: Replace status markdown with plain text file
Repo:    MarcusJellinghaus/mcp_coder
Status:  status-01:created
Branch:  399-vscodeclaude-status-file
Started: 2025-01-15T10:30:00+00:00
URL:     https://github.com/MarcusJellinghaus/mcp_coder/issues/399
==========================================================================
```

### Example with intervention
```
==========================================================================
📝 Issue #399 - vscodeclaude: Replace status markdown with plain text file
Repo:    MarcusJellinghaus/mcp_coder
Status:  status-06:implementing
Branch:  399-vscodeclaude-status-file
Started: 2025-01-15T10:30:00+00:00
Mode:    ⚠️ INTERVENTION
URL:     https://github.com/MarcusJellinghaus/mcp_coder/issues/399
==========================================================================
```

## VERIFICATION

**Note:** Do not run tests after this step - tests will break until Step 3 completes.

Manual verification only: check that the code imports without errors.
