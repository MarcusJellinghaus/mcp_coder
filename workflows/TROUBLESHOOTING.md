# Workflow Troubleshooting Guide

This guide covers common issues encountered when running the implement workflow and their solutions.

## Prerequisites Issues

### Error: "Not a git repository"
**Problem**: The script detects you're not in a git repository.
**Solution**: 
- Ensure you're running the workflow from the project root directory
- Check that `.git` directory exists: `dir .git` (Windows) or `ls -la .git` (Linux/Mac)
- If no git repo exists, initialize one: `git init`

### Error: "pr_info/TASK_TRACKER.md not found"
**Problem**: Required task tracker file is missing.
**Solution**:
- Verify the file exists at `pr_info/TASK_TRACKER.md`
- Check that you're in the correct project directory
- Create the file if missing, following the expected format with Implementation Steps section

## Task Detection Issues

### "No incomplete tasks found - workflow complete"
**Problem**: All tasks are marked as complete `[x]` or no tasks exist.
**Solution**:
- Open `pr_info/TASK_TRACKER.md` and check for tasks marked with `[ ]` (incomplete)
- Verify tasks are in the "Implementation Steps" section
- Add a test task if needed for testing purposes

### Error getting incomplete tasks: [Exception Details]
**Problem**: Task tracker parsing failed.
**Solution**:
- Check `pr_info/TASK_TRACKER.md` format matches expected structure
- Ensure "Implementation Steps" section header exists (case-sensitive)
- Verify checkboxes use correct format: `- [ ]` or `- [x]`
- Check for malformed markdown or special characters

## Prompt Loading Issues

### Error loading prompt template: [Exception Details]
**Problem**: Cannot find or load the Implementation Prompt Template.
**Solution**:
- Verify `src/mcp_coder/prompts/prompts.md` exists
- Check that "Implementation Prompt Template" section exists in the file
- Ensure the section has a code block after the header
- Check file encoding is UTF-8

### Header 'Implementation Prompt Template' not found
**Problem**: Prompt file exists but doesn't contain the expected header.
**Solution**:
- Open `src/mcp_coder/prompts/prompts.md`
- Look for section starting with `# Implementation Prompt Template`
- Check for typos in the header name (case-sensitive)
- Ensure there's a code block (``` fenced) after the header

## LLM Interaction Issues

### Error calling LLM: [Exception Details]
**Problem**: LLM call failed due to authentication, network, or configuration issues.
**Solutions**:
- **Claude Code CLI**: Ensure Claude Code is installed and authenticated
  - Run `claude --version` to check installation
  - Run `claude auth` if authentication is needed
- **Claude Code API**: Verify SDK is installed and authenticated
- **Network**: Check internet connectivity
- **Timeout**: Increase timeout if requests are timing out
- **Rate limits**: Wait and retry if hitting API rate limits

### LLM returned empty response
**Problem**: LLM call succeeded but returned no content.
**Solution**:
- Check the prompt being sent for issues
- Verify LLM service is functioning properly
- Try with a simpler prompt to test connectivity
- Check for content filtering that might block responses

## Formatting Issues

### Error running formatters: [Exception Details]
**Problem**: Code formatting failed.
**Solutions**:
- **black not found**: Install black with `pip install black`
- **isort not found**: Install isort with `pip install isort`
- **Syntax errors**: Fix Python syntax errors before formatting
- **Permission issues**: Ensure files are writable
- **Configuration conflicts**: Check `pyproject.toml` for formatter config issues

### [formatter] formatting failed: [Error Details]
**Problem**: Specific formatter encountered an error.
**Solution**:
- Run the formatter manually to see detailed error: `black .` or `isort .`
- Fix any Python syntax errors in the codebase
- Check formatter configuration in `pyproject.toml`
- Ensure all Python files are syntactically valid

## Git Commit Issues

### Error generating commit message: [Exception Details]
**Problem**: Automatic commit message generation failed.
**Solution**:
- Check that there are staged changes to commit
- Verify LLM integration is working (same as LLM issues above)
- Try running `git status` to see repository state
- Ensure git is properly configured: `git config --list`

### Error committing changes: [Exception Details]
**Problem**: Git commit operation failed.
**Solutions**:
- **No changes to commit**: Check if any files were actually modified
- **Pre-commit hooks**: Check if pre-commit hooks are failing
- **Git configuration**: Ensure user.name and user.email are set
- **File permissions**: Ensure git has permission to write to repository
- **Repository state**: Check for merge conflicts or other git issues

## File System Issues

### Error saving conversation: [Exception Details]
**Problem**: Cannot create or write conversation files.
**Solution**:
- Check permissions on `pr_info/` directory
- Ensure disk space is available
- Verify `pr_info/.conversations/` directory can be created
- Check for file system issues or read-only directories

### Permission denied errors
**Problem**: Insufficient permissions to read/write files.
**Solution**:
- Run workflow with appropriate permissions
- Check file/directory ownership and permissions
- Ensure antivirus isn't blocking file operations
- Try running from a different directory with full permissions

## General Debugging

### Enable Verbose Logging
Add debug prints to the workflow script to trace execution:
```python
# Add at top of implement.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Testing Steps
1. Test task detection: `python -c "from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks; print(get_incomplete_tasks())"`
2. Test prompt loading: `python -c "from mcp_coder.prompt_manager import get_prompt; print(get_prompt('src/mcp_coder/prompts/prompts.md', 'Implementation Prompt Template')[:100])"`
3. Test LLM: `python -c "from mcp_coder.llm_interface import ask_llm; print(ask_llm('Hello', timeout=10))"`
4. Test formatting: `python -c "from mcp_coder.formatters import format_code; from pathlib import Path; print(format_code(Path('.')))"`

### Common Environment Issues
- **Wrong directory**: Always run from project root
- **Python path**: Ensure mcp-coder modules are importable
- **Virtual environment**: Activate the correct Python environment
- **Dependencies**: Run `pip install -r requirements.txt` or equivalent

## Getting Help

If issues persist:
1. Check the full error traceback for specific details
2. Verify your environment matches the prerequisites
3. Test individual components manually using the debugging steps
4. Consider running with reduced functionality to isolate the problem
5. Check project documentation and issue tracker for known problems

## Configuration Validation

### Quick Health Check
Run this from the project root to validate your environment:

```bash
# Check git repository
git status

# Check task tracker
type pr_info\\TASK_TRACKER.md

# Check prompt file  
type src\\mcp_coder\\prompts\\prompts.md

# Check Python imports
python -c "import mcp_coder; print('mcp-coder modules accessible')"

# Check formatters
python -c "import black, isort; print('formatters available')"
```

All checks should pass without errors for the workflow to function properly.