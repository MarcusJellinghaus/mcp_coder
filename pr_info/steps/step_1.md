# Step 1: Delete Duplicate Files and Directory

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 1.

Delete the duplicate labels.json file and its containing directory:
1. Delete workflows/config/labels.json
2. Delete workflows/config/__init__.py
3. Delete the workflows/config/ directory

Verify that tests/workflows/config/ still exists (it's a separate test package).
```

## WHERE

```
workflows/config/labels.json      <- DELETE
workflows/config/__init__.py      <- DELETE
workflows/config/                 <- DELETE (directory)
```

## WHAT

No functions - file deletion only.

## HOW

Use filesystem delete operations:
1. `mcp__filesystem__delete_this_file("workflows/config/labels.json")`
2. `mcp__filesystem__delete_this_file("workflows/config/__init__.py")`
3. Directory will be empty after deletions

## ALGORITHM

```
1. Delete workflows/config/labels.json
2. Delete workflows/config/__init__.py
3. Verify workflows/config/ is empty (auto-removed or manually remove)
4. Verify tests/workflows/config/ still exists with test_labels.json
```

## DATA

No data structures - file operations only.

## Verification

After deletion, confirm:
- `workflows/config/` directory no longer exists
- `tests/workflows/config/test_labels.json` still exists
- `src/mcp_coder/config/labels.json` still exists
