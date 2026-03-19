# Step 2: Fix `langchain_code_api` reconstruction bug in `create_plan.py`

## File
`src/mcp_coder/workflows/create_plan.py`

## Problem
Line 540 reconstructs the llm_method string using:
```python
llm_method = f"{provider}_code_{method}"
```

When `provider="langchain"` and `method="api"` (from `parse_llm_method("langchain")`), this produces `"langchain_code_api"` — which is not a valid llm_method. Valid values are: `claude_code_cli`, `claude_code_api`, `langchain`.

## Fix
Add a conditional for the langchain case:

```python
# Before (line 540):
llm_method = f"{provider}_code_{method}"

# After:
if provider == "langchain":
    llm_method = "langchain"
else:
    llm_method = f"{provider}_code_{method}"
```

## Note
A broader cleanup (removing `method` parameter, dropping `claude_code_api` support) is tracked in a separate task. This fix is minimal and correct for this bug.
