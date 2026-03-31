# Step 2: Extend `BranchStatusReport` with PR fields

## LLM Prompt
> Read `pr_info/steps/summary.md` for context. Implement Step 2: Add optional PR fields to `BranchStatusReport` dataclass and update display methods. Write tests first (TDD), then implement. Run all code quality checks after.

## WHERE
- **Test**: `tests/checks/test_branch_status_pr_fields.py` (new file)
- **Implementation**: `src/mcp_coder/checks/branch_status.py`

## WHAT

### Extend `BranchStatusReport` dataclass:
```python
@dataclass(frozen=True)
class BranchStatusReport:
    # ... existing fields ...
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_found: Optional[bool] = None
```

### Update `format_for_human()`:
Add PR section between branch info and CI status (only when `pr_found is not None`).

### Update `format_for_llm()`:
Add `PR=#123` to status summary line (only when `pr_found is not None`).

### Update `create_empty_report()`:
Include `pr_number=None, pr_url=None, pr_found=None` defaults.

## HOW
- All new fields have defaults (`None`) so existing callers are unaffected
- Display conditional: only show PR section when `pr_found is not None` (distinguishes "not checked" from "checked, not found")

## ALGORITHM (format_for_human PR section)
```
1. If self.pr_found is None: skip (PR check not requested)
2. If self.pr_found is True: show "PR: ✅ #123 (url)"
3. If self.pr_found is False: show "PR: ❌ No PR found"
4. Insert after "Branch Status Report" header, before CI section
```

## ALGORITHM (format_for_llm PR section)
```
1. If self.pr_found is None: no change to status_summary
2. If self.pr_found is True: append ", PR=#123" to status_summary
3. If self.pr_found is False: append ", PR=NOT_FOUND" to status_summary
```

## DATA
- Three new optional fields on frozen dataclass (all default `None`)
- No changes to `collect_branch_status()` — PR fields are set by the command layer

## TESTS (`test_branch_status_pr_fields.py`)

| Test | Description |
|------|-------------|
| `test_report_without_pr_fields` | Default `None` fields — human/LLM output unchanged (no PR section) |
| `test_report_with_pr_found` | `pr_found=True, pr_number=123, pr_url="..."` — human shows PR line, LLM shows `PR=#123` |
| `test_report_with_pr_not_found` | `pr_found=False` — human shows "No PR found", LLM shows `PR=NOT_FOUND` |
| `test_empty_report_has_pr_defaults` | `create_empty_report()` returns `None` for all PR fields |

## COMMIT
`feat(branch_status): add optional PR fields to BranchStatusReport`
