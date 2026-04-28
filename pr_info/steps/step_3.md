# Step 3 — Switch `ci.yml` mypy matrix entry to lean `[typecheck]` install

> Read `pr_info/steps/summary.md` first for full context. **Depends on Step 1** (the `[typecheck]` extra must already exist in `pyproject.toml`).

## Goal

Make the new `[typecheck]` extra **load-bearing in regular CI** by having the `mypy` matrix entry install only `.[typecheck]` instead of the shared `.[dev,langchain]`. This is what catches drift when the transitive mypy disappears from `[dev]`.

The other 7 matrix entries (`black`, `isort`, `pylint`, `ruff-docstrings`, `unit-tests`, `integration-tests`, `file-size`) and the entire `architecture` job remain **untouched** — per the issue's explicit constraint.

## WHERE

- **Modify** `.github/workflows/ci.yml` — two surgical changes inside the `test` job only.

## WHAT

### Change 1 — add `install` field to the mypy matrix entry only

Find the matrix entry (currently around line 102):

```yaml
          - {name: "mypy", cmd: "mypy --version && mypy --strict src tests"}
```

Change it to:

```yaml
          - {name: "mypy", install: ".[typecheck]", cmd: "mypy --version && mypy --strict src tests"}
```

**Do not** add `install` to any other matrix entry. The fallback expression in Change 2 handles them.

### Change 2 — switch the shared install step to use the matrix field with a fallback

Find the install step in the `test` job (currently around lines 124–125):

```yaml
      - name: Install dependencies
        run: uv pip install --system ".[dev,langchain]"
```

Change it to:

```yaml
      - name: Install dependencies
        run: uv pip install --system "${{ matrix.check.install || '.[dev,langchain]' }}"
```

When `matrix.check.install` is unset (the 7 untouched entries), it evaluates to empty string and `||` returns the original `.[dev,langchain]`. When set (mypy entry only), it returns `.[typecheck]`.

### Do NOT touch

- The `architecture` job (separate matrix, separate install step) — leave fully unchanged.
- The `check-forbidden-folders` job — unrelated.
- The "Install latest GitHub dependencies" step (the upstream-from-git installs) — unchanged in both jobs.
- All other matrix entries in the `test` job — no `install` field added.

## HOW

- Use `mcp__workspace__edit_file` with the exact `old_string` / `new_string` for both edits — the matrix entry line is unique, and the install step text is unique within the `test` job.
- After both edits, the diff should be exactly **2 lines changed** (one in the matrix block, one in the install step).

## ALGORITHM (CI behavior after change)

```
For each matrix entry in `test` job:
    if entry.install is set:        # mypy only
        install -> ".[typecheck]"   # ~mypy + types stubs only
    else:                            # other 7 entries
        install -> ".[dev,langchain]"  # full dev set, unchanged
    Then run entry.cmd
```

The mypy job will now see only: mypy, the 3 upstream-from-git packages, type stubs (`types-pyperclip`, `types-requests`, `types-tabulate`), and base dependencies of `mcp-coder` itself. It will **not** see langchain/mlflow/textual etc. — but the existing `[[tool.mypy.overrides]]` already handle those modules via `ignore_missing_imports` / `follow_imports = "skip"`.

## DATA

- **Matrix entry shape (mypy):** `{name: str, install: str, cmd: str}`
- **Matrix entry shape (other 7):** `{name: str, cmd: str}` — unchanged
- **Install expression:** `${{ matrix.check.install || '.[dev,langchain]' }}` resolves to `".[typecheck]"` for mypy, `".[dev,langchain]"` for others.

## Verification

After editing, run **all three** quality checks per CLAUDE.md:

```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```

The mypy run here uses the local environment (still has full dev deps installed) — it will not fully replicate the lean CI install, but it confirms the source/types still type-check.

**Real CI verification (acceptance criterion 5)** happens when the PR runs `Python CI`. If the mypy matrix entry fails because something needs to be in `[typecheck]` that isn't, fix it then by either:
- Adding the missing stub package to the `[types]` group, OR
- Adding a new `[[tool.mypy.overrides]]` entry with `ignore_missing_imports = true`.

Do **not** revert to `.[dev,langchain]` for mypy — that defeats the whole purpose of the issue.

## Commit

One commit:
```
ci: lean .[typecheck] install for mypy matrix entry (issue #922)

Mypy entry now installs .[typecheck] instead of the shared
.[dev,langchain]. Other 7 matrix entries and the architecture job
unchanged. Achieved via a per-entry `install` field plus a `||`
fallback in the install step — no entries other than mypy touched.

This makes the new [typecheck] extra load-bearing: if mypy is ever
dropped as a transitive of [dev], CI fails loudly instead of silently
losing type-checking.
```

## LLM prompt for this step

> Implement Step 3 of `pr_info/steps/summary.md`. Read both `pr_info/steps/summary.md` and `pr_info/steps/step_3.md` for full context. Step 1 must already be merged (the `[typecheck]` extra must exist in `pyproject.toml`).
>
> Make exactly two surgical edits to `.github/workflows/ci.yml`:
> 1. Add `install: ".[typecheck]"` to the `mypy` matrix entry only.
> 2. Change the `Install dependencies` step in the `test` job to `uv pip install --system "${{ matrix.check.install || '.[dev,langchain]' }}"`.
>
> Do NOT modify the other 7 matrix entries, the `architecture` job, the `check-forbidden-folders` job, or the "Install latest GitHub dependencies" step. The diff should be exactly 2 lines changed.
>
> Use only MCP tools (`mcp__workspace__edit_file`). After editing, run the three required quality checks. Make exactly one commit with the message in step_3.md.
