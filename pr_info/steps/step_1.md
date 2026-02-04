# Step 1: Update Templates

## LLM Prompt

```
Implement Step 1 of Issue #399 (see pr_info/steps/summary.md for context).

Update the template strings in templates.py:
1. Replace STATUS_FILE_TEMPLATE with plain text banner format
2. Update GITIGNORE_ENTRY to use .txt instead of .md
3. Add second task to TASKS_JSON_TEMPLATE for auto-opening status file
4. Remove INTERVENTION_ROW (no longer needed)

Follow TDD: update tests first, then implement.
```

## WHERE

**File:** `src/mcp_coder/workflows/vscodeclaude/templates.py`

**Lines to modify:**
- `STATUS_FILE_TEMPLATE` (lines 168-181)
- `INTERVENTION_ROW` (lines 184-186) - DELETE
- `GITIGNORE_ENTRY` (lines 192-197)
- `TASKS_JSON_TEMPLATE` (lines 152-165)

## WHAT

### 1. STATUS_FILE_TEMPLATE

**Current signature:** Template with placeholders: `{issue_number}`, `{title}`, `{status_emoji}`, `{status_name}`, `{repo}`, `{branch}`, `{started_at}`, `{intervention_row}`, `{issue_url}`

**New signature:** Template with placeholders: `{status_emoji}`, `{issue_number}`, `{title}`, `{repo}`, `{status_name}`, `{branch}`, `{started_at}`, `{intervention_line}`, `{issue_url}`

### 2. GITIGNORE_ENTRY

**Change:** `.vscodeclaude_status.md` → `.vscodeclaude_status.txt`

### 3. TASKS_JSON_TEMPLATE

**Current signature:** Template with placeholder: `{script_path}`

**New signature:** Same placeholder, but template contains two tasks

### 4. INTERVENTION_ROW → Remove entirely

Replace with inline `{intervention_line}` in the new STATUS_FILE_TEMPLATE

## HOW

Direct string replacement in template constants. No imports or decorators needed.

## ALGORITHM

```
# STATUS_FILE_TEMPLATE
1. Use plain text banner format with === borders
2. Include: emoji, issue number, title on first content line
3. Include: Repo, Status, Branch, Started, optional Mode (intervention), URL
4. Use {intervention_line} placeholder (empty string or "Mode:    ⚠️ INTERVENTION\n")

# TASKS_JSON_TEMPLATE  
1. Keep existing startup task
2. Add second task "Open Status File"
3. Use "shell" type with "code" command to open file
4. Both tasks have runOn: folderOpen
```

## DATA

### New STATUS_FILE_TEMPLATE

```python
STATUS_FILE_TEMPLATE = """==========================================================================
{status_emoji} Issue #{issue_number} - {title}
Repo:    {repo}
Status:  {status_name}
Branch:  {branch}
Started: {started_at}
{intervention_line}URL:     {issue_url}
==========================================================================
"""
```

### New GITIGNORE_ENTRY

```python
GITIGNORE_ENTRY = """
# VSCodeClaude session files (auto-generated)
.vscodeclaude_status.txt
.vscodeclaude_analysis.json
.vscodeclaude_start.bat
.vscodeclaude_start.sh
"""
```

### New TASKS_JSON_TEMPLATE

```python
TASKS_JSON_TEMPLATE = """{{
    "version": "2.0.0",
    "tasks": [
        {{
            "label": "VSCodeClaude Startup",
            "type": "shell",
            "command": "{script_path}",
            "presentation": {{
                "reveal": "always",
                "panel": "new",
                "focus": true
            }},
            "runOptions": {{
                "runOn": "folderOpen"
            }},
            "problemMatcher": []
        }},
        {{
            "label": "Open Status File",
            "type": "shell",
            "command": "code",
            "args": ["${{workspaceFolder}}/.vscodeclaude_status.txt"],
            "presentation": {{
                "reveal": "never"
            }},
            "runOptions": {{
                "runOn": "folderOpen"
            }},
            "problemMatcher": []
        }}
    ]
}}
"""
```

## VERIFICATION

**Note:** Do not run tests after this step - tests will break until Step 3 completes.

Quick syntax check only:
```bash
python -c "from mcp_coder.workflows.vscodeclaude.templates import STATUS_FILE_TEMPLATE, GITIGNORE_ENTRY, TASKS_JSON_TEMPLATE; print('Templates loaded OK')"
```
