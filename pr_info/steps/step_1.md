# Step 1: Delete `tools/reinstall.bat`

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Remove the obsolete PyPI (non-editable) reinstall script. It is not part of the developer workflow and only causes confusion alongside `reinstall_local.bat`.

## Changes

### DELETE: `tools/reinstall.bat`

Delete the entire file.

## Verification

- No other file references `reinstall.bat` (only `reinstall_local.bat` is referenced from `claude_local.bat` and `icoder_local.bat`)
- All quality checks pass (pylint, pytest, mypy)

## Commit

```
chore: delete obsolete PyPI reinstall script (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Delete tools/reinstall.bat. Verify no other files reference it (search for "reinstall.bat" 
excluding reinstall_local.bat references). Run all quality checks.
```
