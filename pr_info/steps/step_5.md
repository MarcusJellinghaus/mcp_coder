# Step 5: Update `pyproject.toml` — enable warnings in CI (final commit)

## Goal
Replace the blanket `disable = ["W", "C", "R"]` with selective disables that expose
all W-category warnings while permanently suppressing the ones that are intentional
project patterns. This is the **last commit** — all warnings must already be zero
or inline-disabled before this lands.

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

[tool.pylint.MASTER]
# Disable test-specific W warnings that are standard pytest patterns
per-file-ignores = [
    "tests/**/*.py:W0212",   # protected-access — legitimate test inspection
    "tests/**/*.py:W0613",   # unused-argument — pytest fixtures (injected by name)
    "tests/**/*.py:W0611",   # unused-import — fixture imports, conftest re-exports
    "tests/**/*.py:W0404",   # reimported — reimports across test functions
]
```

## HOW

The `per-file-ignores` entry under `[tool.pylint.MASTER]` uses pylint's native
glob-based per-file suppress feature (supported in pylint 3.x via pyproject.toml).

After this change, `pylint src/ tests/` with no extra flags will:
- Report E and F (errors/fatals) — always
- Report W — but suppress W1203, W0621, W0511 globally and W0212/W0613/W0611/W0404 for tests/
- Suppress C and R — unchanged

The CI pipeline already calls pylint — this config change makes warnings visible there.

## ALGORITHM

```
Open pyproject.toml
Find [tool.pylint.messages_control]
Replace disable = ["W", "C", "R"] with the new selective disable list
Add per-file-ignores under [tool.pylint.MASTER]
Verify syntax: run pylint src/ tests/ and confirm zero warnings reported
Run pytest fast unit tests — confirm no regressions
Run mypy — confirm clean
```

## DATA

No code changes. Config-only change.
This commit is the acceptance-criteria gate:
> `pylint src/ tests/` with new config reports **zero warnings** (all fixed or inline-disabled)

## Verification Checklist

Before committing this step:
1. Run `pylint src/ tests/` (no extra flags) → must show 0 warnings
2. Run pytest fast unit tests → must pass
3. Run mypy → must be clean
4. Run `./tools/ruff_check.sh` → must pass

---

## LLM Prompt

```
Please implement Step 5 of the pylint warning cleanup described in
`pr_info/steps/summary.md` and `pr_info/steps/step_5.md`.

This is the FINAL commit. All previous steps (1–4) must already be committed
and CI-green before this step is applied.

Change ONLY `pyproject.toml`:

In `[tool.pylint.messages_control]`:
  Replace:
    disable = ["W", "C", "R"]
  With:
    disable = [
        "C",
        "R",
        "W1203",
        "W0621",
        "W0511",
    ]
  Keep:
    enable = ["R0401"]

Add under `[tool.pylint.MASTER]` (create the section if it doesn't exist,
but preserve the existing init-hook and extension-pkg-allow-list entries):
    per-file-ignores = [
        "tests/**/*.py:W0212",
        "tests/**/*.py:W0613",
        "tests/**/*.py:W0611",
        "tests/**/*.py:W0404",
    ]

After making the change:
- Run `pylint src/ tests/` with NO extra --disable flags
- The result must show zero warnings (W-category)
- Run pytest (fast unit tests) — must pass
- Run mypy — must be clean
- Run ./tools/ruff_check.sh — must pass

If any warnings appear, DO NOT commit — go back and fix them first.
```
