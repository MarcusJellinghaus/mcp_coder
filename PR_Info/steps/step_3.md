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
def check_prerequisites() -> bool           # NEW: Verify dependencies
def get_next_task() -> str | None  
def save_conversation(content: str, step_num: int) -> None
def run_formatters() -> bool                # Enhanced: Return success status
def commit_changes() -> bool                # Enhanced: Return success status
def log_step(message: str) -> None          # NEW: Consistent logging
```

## HOW
### Integration Points
```python
# Imports - Direct API calls only, no subprocess/CLI calls
sys.path.append('../src')  # Simple path addition
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.llm_interface import ask_llm  
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks
from mcp_coder.formatters import format_code
from mcp_coder.utils.git_operations import commit_all_changes
from mcp_coder.cli.commands.commit import generate_commit_message_with_llm
```

## ALGORITHM
```
1. Check prerequisites (git status, task tracker exists)
2. Check for incomplete tasks (entrance condition)
3. Get implementation prompt template using get_prompt()
4. Call LLM with prompt using ask_llm()  
5. Save conversation to pr_info/.conversations/step_N.md
6. Run formatters (black, isort) using existing format_code()
7. Commit changes using generate_commit_message_with_llm() and commit_all_changes()
8. Early exit on failures with clear error messages
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
# Conversation file naming: step_1.md, step_1_2.md, step_1_3.md (incremental numbering)
```

## Implementation Notes
- Enhanced error handling with meaningful messages and early exit
- Use existing APIs without modification
- Consistent logging format with timestamps
- Single task execution - no loops
- Basic file versioning for conversations
- Return status codes for better flow control

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
