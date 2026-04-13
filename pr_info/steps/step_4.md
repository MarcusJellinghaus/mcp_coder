# Step 4: Import-linter contract updates

**Commit message:** `adopt mcp-coder-utils: update import-linter contracts for shim boundary`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step updates `.importlinter` to enforce the shim boundary and tighten existing contracts.

## WHERE

- `.importlinter`

## WHAT

Four changes in one file, one commit:

### 4a. Add new contract: `mcp_coder_utils_isolation`
Only the 3 shim files may import from `mcp_coder_utils`. This enforces the shim boundary — no other module should bypass the local shims.

```ini
[importlinter:contract:mcp_coder_utils_isolation]
name = MCP Coder Utils Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    mcp_coder_utils
ignore_imports =
    mcp_coder.utils.subprocess_runner -> mcp_coder_utils
    mcp_coder.utils.subprocess_streaming -> mcp_coder_utils
    mcp_coder.utils.log_utils -> mcp_coder_utils
```

### 4b. Update `subprocess_isolation` contract
The shim files no longer import `subprocess` directly. Also, test files `test_subprocess_runner.py` and `test_subprocess_runner_real.py` are deleted in step 5.

**Remove these ignore_imports lines:**
- `mcp_coder.utils.subprocess_runner -> subprocess`
- `mcp_coder.utils.subprocess_streaming -> subprocess`
- `tests.utils.test_subprocess_runner -> subprocess`
- `tests.utils.test_subprocess_runner_real -> subprocess`

**Keep:**
- `mcp_coder.utils.mcp_verification -> subprocess`
- `tests.utils.test_mcp_verification -> subprocess`

> **Note:** If import-linter traces through re-exports and still sees subprocess via the shim, we may need to keep the shim exceptions. Run `lint-imports` to verify. Adjust as needed.

### 4c. Tighten `structlog_isolation` contract
The `log_utils` shim no longer imports `structlog` directly.

**Remove the `ignore_imports` section entirely** (or remove the line `mcp_coder.utils.log_utils -> structlog`).

### 4d. Tighten `jsonlogger_isolation` contract
The `log_utils` shim no longer imports `pythonjsonlogger` directly.

**Remove the `ignore_imports` section entirely** (or remove the line `mcp_coder.utils.log_utils -> pythonjsonlogger`).

## HOW

Edit `.importlinter` — all four changes in one edit pass.

## ALGORITHM

```
1. Add mcp_coder_utils_isolation contract (forbidden type)
2. In subprocess_isolation: remove 4 ignore_imports lines for shims + deleted tests
3. In structlog_isolation: remove ignore_imports section
4. In jsonlogger_isolation: remove ignore_imports section
5. Run lint-imports to verify all contracts pass
6. If any contract fails, adjust (e.g. keep exceptions if linter traces through re-exports)
```

## DATA

No code changes. Configuration only.

## VERIFICATION

- Run `lint-imports` — all contracts must pass
- If `subprocess_isolation` fails because import-linter traces through re-exports, add back the shim exceptions
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

Implement step 4: Update .importlinter with all four contract changes:
(a) add mcp_coder_utils_isolation, (b) update subprocess_isolation,
(c) tighten structlog_isolation, (d) tighten jsonlogger_isolation.
Run lint-imports to verify. Adjust if needed. Run all checks after.
```
