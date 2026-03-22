# Step 14: pyproject.toml config change (LAST — enables warnings in CI)

## Goal
Replace the blanket `disable = ["W", "C", "R"]` with selective disables that expose
all W-category warnings. This is the **last commit** — all warnings must already be
zero or inline-disabled before this lands.

## WHERE — Files Modified

- `pyproject.toml` — one section change only

## WHAT

**Current config (`[tool.pylint.messages_control]`):**
```toml
disable = ["W", "C", "R"]
enable = ["R0401"]
```

**New config:**
```toml
[tool.pylint.messages_control]
disable = [
    "C",       # conventions — not enabled in this project
    "R",       # refactor suggestions — not enabled in this project
    "W1203",   # logging-fstring-interpolation — project uses f-strings for readability
    "W0621",   # redefined-outer-name — standard pytest fixture pattern
    "W0511",   # fixme/TODO — informational only, not a quality gate
]
enable = ["R0401"]
```

**Append to the existing `[tool.pylint.main]` section** (do NOT create a new `[tool.pylint.main]` header — TOML forbids duplicate section headers):
```toml
# Disable test-specific W warnings that are standard pytest patterns
per-file-ignores = [
    "tests/**/*.py:W0212",   # protected-access — legitimate test inspection
    "tests/**/*.py:W0613",   # unused-argument — pytest fixtures (injected by name)
    "tests/**/*.py:W0611",   # unused-import — fixture imports, conftest re-exports
    "tests/**/*.py:W0404",   # reimported — reimports across test functions
]
```

**IMPORTANT:** `pyproject.toml` already has a `[tool.pylint.main]` section. Append `per-file-ignores` there. Do NOT add a second `[tool.pylint.main]` header — TOML does not allow duplicate section headers and it will cause a parse error.

## Verification Checklist

Before committing this step:
1. Run `pylint src/ tests/` (no extra flags) -> must show 0 warnings
2. Run pytest fast unit tests -> must pass
3. Run mypy -> must be clean
4. Run `./tools/ruff_check.sh` -> must pass

---

## LLM Prompt

```
Please implement Step 14 (FINAL) of the pylint warning cleanup.
See pr_info/steps/step_14.md.

Change ONLY pyproject.toml:
- In [tool.pylint.messages_control]: replace disable = ["W", "C", "R"] with selective list
- Append per-file-ignores to the EXISTING [tool.pylint.main] section (do NOT create a duplicate header)
- Keep enable = ["R0401"]

After making the change, run pylint src/ tests/ with NO extra flags — must show 0 warnings.
Run pytest, mypy, and ./tools/ruff_check.sh — all must pass.
```
