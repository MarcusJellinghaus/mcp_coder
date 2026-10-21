# Step 2: Run the import-health test against upstream main in CI

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Step 1 is done (`tests/test_module_imports.py` exists). Implement step 2
> only: edit `.github/workflows/upstream-mypy-check.yml` as specified. No
> Python changes. Run pylint, mypy and the fast unit tests to confirm nothing
> regressed, then make exactly one commit.

## WHERE

- Modify `.github/workflows/upstream-mypy-check.yml` (keep the file name — the
  upstream repos' dispatch only sends the event type).

## WHAT

1. Job id `mypy-against-upstream-main` → `upstream-compat`.
2. Job `name:` → `upstream-compat-${{ github.event.client_payload.upstream || github.event.inputs.upstream || github.event_name }}`.
3. Install step: add `id: install`; rename to
   `Install mcp_coder with typecheck, test and langchain extras`; command
   `uv pip install --system ".[typecheck,test,langchain]"`. Keep it **after**
   the upstream git installs; update the order comment to mention the new extras
   (`test` needed for pytest-xdist since `addopts` has `-n auto`).
4. mypy step: add `if: ${{ !cancelled() && steps.install.outcome == 'success' }}`.
5. New step after mypy:
   ```yaml
   - name: Import every mcp_coder module (strict)
     if: ${{ !cancelled() && steps.install.outcome == 'success' }}
     env:
       MCP_CODER_IMPORT_TEST_STRICT: "1"
     run: pytest tests/test_module_imports.py
   ```
6. Header comment: say the workflow runs mypy --strict **and** a runtime
   import check of every module against upstream main.

## HOW

- The `if:` on both check steps makes each run even when the other fails,
  while still skipping both if install failed.
- No Python or docs changes (the old job name appears nowhere else).

## ALGORITHM

None — configuration only.

## DATA

None.

## Checks

- Validate YAML structure by reading the file back (indentation, `id`, `if`, `env`).
- Commit message: `ci: run import-health check against upstream main (#1246)`
