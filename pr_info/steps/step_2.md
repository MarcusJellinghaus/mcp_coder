# Step 2: Add always-run editable install to VENV_SECTION_WINDOWS

> **Context**: See `pr_info/steps/summary.md` for the full plan.
> This step adds `uv pip install -e . --no-deps` to the venv template so that the
> editable install runs on every launch, regardless of `--from-github`.

## LLM Prompt

```
Read pr_info/steps/summary.md for context, then implement Step 2.

Add `uv pip install -e . --no-deps` to the end of `VENV_SECTION_WINDOWS` in
templates.py, after the environment setup is complete (after the if/else
activation block, before the final echo lines). Write tests first (TDD), then
implement. Run all three code quality checks after changes.
```

## Files to Modify

### Tests (write first)

**`tests/workflows/vscodeclaude/test_templates.py`** — Add test:
- `test_venv_section_runs_editable_install`: Assert `"uv pip install -e . --no-deps"`
  is present in `VENV_SECTION_WINDOWS`.

### Implementation

**`src/mcp_coder/workflows/vscodeclaude/templates.py`**

- WHERE: `VENV_SECTION_WINDOWS` template string
- WHAT: Append `uv pip install -e . --no-deps` after venv activation, before final echo
- HOW: Insert batch commands after `set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"` and
  before the final "Environment setup complete" echo block

```
... existing venv activation ...

set "PATH=%MCP_CODER_VENV_PATH%;%PATH%"

REM Install project in editable mode (ensures current code is always used)
uv pip install -e . --no-deps

echo Environment setup complete.
...
```

## Algorithm (pseudocode)

```
# In VENV_SECTION_WINDOWS, after PATH is set:
1. Add "REM Install project in editable mode" comment
2. Add "uv pip install -e . --no-deps" command
3. Keep existing echo lines after
```

## Verification

- Existing template tests still pass
- New test confirms `-e .` is in the template
- `test_venv_section_installs_dev_dependencies` still passes (no conflict)
- pylint, mypy, pytest all green
