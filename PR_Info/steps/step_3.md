# Step 3: Create Simple Implement Workflow Script

## Objective
Create the core implement.py workflow script that orchestrates existing mcp-coder functionality to automate the implementation process.

## WHERE
- `workflows/implement.py` - Main workflow script
- Update `workflows/implement.bat` - Proper batch command

## WHAT
### Main Functions
```python
def main() -> None
def get_next_task() -> str | None  
def save_conversation(content: str, step_num: int) -> None
def run_formatters() -> None
def commit_changes() -> None
```

## HOW
### Integration Points
```python
# Imports
sys.path.append('../src')  # Simple path addition
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.llm_interface import ask_llm  
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks
from mcp_coder.formatters import format_code
import subprocess  # For commit command
```

## ALGORITHM
```
1. Check for incomplete tasks (entrance condition)
2. Get implementation prompt template using get_prompt()
3. Call LLM with prompt using ask_llm()  
4. Save conversation to pr_info/.conversations/step_N.md
5. Run formatters (black, isort) using existing format_code()
6. Commit changes using subprocess call to mcp-coder commit auto
```

## DATA
### Input/Output
- **Input**: Task tracker state, prompt template
- **Process**: LLM conversation, code formatting, git operations
- **Output**: 
  - Conversation file: `pr_info/.conversations/step_N.md` (string content)
  - Formatted code files  
  - Git commit with auto-generated message
  - Console output with timestamps

### Data Structures
```python
PR_INFO_DIR: str = "pr_info"
CONVERSATIONS_DIR: str = f"{PR_INFO_DIR}/.conversations"
incomplete_tasks: List[str]  # From task tracker
response: str  # From LLM
```

## Implementation Notes
- Keep error handling minimal (KISS principle)
- Use existing APIs without modification
- Simple timestamp logging with print statements
- Single task execution - no loops
- Basic file versioning for conversations

## LLM Prompt  
```
Please look at pr_info/steps/summary.md and implement Step 3.

Create workflows/implement.py with:
1. Simple script that orchestrates existing mcp-coder functionality
2. Check for tasks using task_tracker 
3. Get prompt using get_prompt()
4. Call LLM using ask_llm()
5. Save conversation to pr_info/.conversations/
6. Format code using formatters
7. Commit using subprocess call to mcp-coder commit auto
8. Update implement.bat to run the script

Keep it simple - just orchestrate existing APIs. Add timestamp logging between steps.
Focus only on Step 3 implementation.
```
