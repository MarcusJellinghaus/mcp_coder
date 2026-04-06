# Step 1: Delete `tools/reinstall.bat`

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Remove the obsolete PyPI (non-editable) reinstall script. It is not part of the developer workflow and only causes confusion alongside `reinstall_local.bat`.

## Changes

### DELETE: `tools/reinstall.bat`

Delete the entire file.

### MODIFY: `tools/reinstall_local.bat`

Lines 4 and 11 contain comments referencing "End-users should use tools\reinstall.bat instead". Remove these stale references since `reinstall.bat` no longer exists.

### MODIFY: `docs/repository-setup.md`

Remove the `reinstall.bat` row from the tools table.

## Verification

- No remaining references to `reinstall.bat` in the codebase
- All quality checks pass (pylint, pytest, mypy)

## Commit

```
chore: delete obsolete PyPI reinstall script (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Delete tools/reinstall.bat. Remove stale references to reinstall.bat in 
tools/reinstall_local.bat (lines 4 and 11) and remove the reinstall.bat row from 
the tools table in docs/repository-setup.md. Search for any remaining references. 
Run all quality checks.
```
