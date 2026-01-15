# Step 1: Migrate to uv and Update Dependencies

## LLM Prompt

```
Read pr_info/steps/summary.md for context on Issue #284.

Implement Step 1: Migrate from pip to uv for dependency installation in the CI workflow.

Changes to make in .github/workflows/ci.yml:
1. Add astral-sh/setup-uv@v4 action after checkout in both `test` and `architecture` jobs
2. Replace pip installation commands with uv

Do not modify matrix commands yet - that's Step 2.
```

## WHERE

| File | Action |
|------|--------|
| `.github/workflows/ci.yml` | Modify |

## WHAT

### Add uv Setup Step (both jobs)

Add after `actions/checkout@v4`:

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4
```

### Replace Dependency Installation (both jobs)

**Before:**
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    python -m pip install .
    python -m pip install .[dev]
```

**After:**
```yaml
- name: Install dependencies
  run: uv pip install --system ".[dev]"
```

## HOW

### Integration Points

1. `astral-sh/setup-uv@v4` - Official uv GitHub Action
2. `uv pip install --system` - Install to system Python (not virtualenv)
3. `".[dev]"` - Install package with dev dependencies (includes types via recursive dependency)

### Why `--system` Flag

GitHub Actions runners use system Python. The `--system` flag tells uv to install packages to the system Python environment rather than creating a virtualenv.

## DATA

### Optional Dependencies Installed

From `pyproject.toml`:

```toml
[project.optional-dependencies]
types = [
    "types-pyperclip",
    "types-requests>=2.28.0",
]

dev = [
    "mcp-coder[types,test,mcp]",  # includes types
    "import-linter>=2.0",
    "pycycle>=0.0.8",
    "tach>=0.6.0",
    "vulture>=2.14",
]
```

## ALGORITHM

```
1. Checkout repository (existing)
2. Setup Python 3.11 (existing)
3. Install uv via astral-sh/setup-uv@v4 (NEW)
4. Install dependencies with uv: ".[dev,types]" (MODIFIED)
5. Run checks (existing, modified in Step 2)
```

## Validation

After implementation, the CI should:
- Successfully install uv
- Successfully install all dependencies including type stubs
- Complete faster than before (uv is ~10-100x faster than pip)
