# Fix SystemMessage .get() AttributeError in Prompt Command

## Problem Summary
The prompt command fails with `'SystemMessage' object has no attribute 'get'` when using `--verbosity raw` because the code tries to call dictionary methods on Claude SDK message objects.

## Root Cause Analysis
- **Location**: `src/mcp_coder/cli/commands/prompt.py:158` in `_format_verbose()`
- **Issue**: Code assumes `raw_messages` contains dictionaries, but they're actually Claude SDK objects (`SystemMessage`, `AssistantMessage`, `ResultMessage`)
- **Error**: `message.get("role")` fails because SDK objects don't have `.get()` method

## Technical Context
- Tests mock `raw_messages` with dictionaries for simplicity
- Real SDK returns proper message objects with attributes (not dictionary keys)
- Need dual compatibility: dictionary format (tests) + SDK objects (production)

## Solution Strategy
1. **Type Detection**: Check if message is dict or SDK object
2. **Unified Access**: Create helper functions to extract data from both formats
3. **Backward Compatibility**: Maintain existing test expectations
4. **Error Prevention**: Add proper type checking and fallbacks

## Success Criteria
- ✅ `mcp-coder prompt "test" --verbosity raw` works without errors
- ✅ All existing tests continue to pass
- ✅ Tool interaction extraction works for both dict and SDK objects
- ✅ JSON serialization works for both formats in raw output

## Implementation Approach
- **Step 1**: Add comprehensive test coverage for the actual error scenario
- **Step 2**: Create message format detection and unified access utilities
- **Step 3**: Fix `_format_verbose()` to handle both message formats
- **Step 4**: Fix `_format_raw()` to properly serialize SDK objects
- **Step 5**: Add integration test to prevent regression

This fix ensures the prompt command works reliably with real Claude SDK responses while maintaining test compatibility.
