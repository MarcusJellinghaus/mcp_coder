# Step 2: Add 9 GitHub label mappings to `_LABEL_MAP` + formatting tests

**See:** `pr_info/steps/summary.md` for full context.

## LLM Prompt

> Add 9 GitHub check key → human label mappings to `_LABEL_MAP` in
> `src/mcp_coder/cli/commands/verify.py`. Then add tests in
> `test_verify_format_section.py` that verify `_format_section("GITHUB", ...)`
> renders these labels correctly.
> See `pr_info/steps/summary.md` for full context.

## WHERE

- `src/mcp_coder/cli/commands/verify.py` — `_LABEL_MAP` dict (line ~159)
- `tests/cli/commands/test_verify_format_section.py` — new test class

## WHAT

Add to `_LABEL_MAP`:

```python
# GitHub section
"token_configured": "Token configured",
"authenticated_user": "Authenticated user",
"repo_url": "Repo URL",
"repo_accessible": "Repo accessible",
"branch_protection": "Branch protection",
"ci_checks_required": "CI checks required",
"strict_mode": "Strict mode",
"force_push": "Force push",
"branch_deletion": "Branch deletion",
```

## HOW

- Append entries to the existing `_LABEL_MAP` dict after the MLflow section comment
- Add a `# GitHub section` comment for readability (matches existing pattern)

## ALGORITHM

No logic — data-only change.

## DATA

- Keys: the 9 strings from `verify_github()` result dict
- Values: human-readable labels for terminal display

## TESTS (write first)

Add `TestGitHubLabelMappings` class in `test_verify_format_section.py`:

1. `test_all_github_keys_in_label_map` — assert all 9 keys exist in `_LABEL_MAP`
2. `test_format_section_renders_github_labels` — call `_format_section("GITHUB", sample_result, symbols)` with a few entries (e.g. `token_configured`, `repo_accessible`) and assert the human labels appear in output
3. `test_format_section_github_warning_entry` — entry with `ok=None` renders `[WARN]` symbol (for branch protection warnings)

Use existing `_symbols()` helper pattern from the file.
