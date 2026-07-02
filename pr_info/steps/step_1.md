# Step 1 — Langchain backend readiness warning on the claude-active path

**Read first:** `pr_info/steps/summary.md` (behavior matrix, design rationale, scope).

This is the only implementation step. It is a single cohesive feature (one helper + its wiring
+ its tests) and produces **exactly one commit**. The three warning/no-warning cases are branches
of one helper, not independent parts, so they are not split further.

---

## WHERE
- **Implementation:** `src/mcp_coder/cli/commands/verify.py`
  - New module-level private helper `_print_langchain_readiness_warning`.
  - One added call inside the existing `else` branch of the
    `active_provider == "langchain"` gate (~line 778-779, inside `execute_verify`).
- **Tests:** `tests/cli/commands/test_verify_integration.py`
  - Three new integration tests in the same test class as
    `test_claude_fallback_note_when_claude_active`.

## WHAT
```python
def _print_langchain_readiness_warning(symbols: dict[str, str]) -> None:
    """Warn (exit-neutral) when the configured langchain backend module is missing.

    Runs regardless of active provider. Prints nothing when langchain is not
    configured, or when a known backend's module is installed. Builds no result
    dict — it only prints, so it can never affect the exit code.
    """
```
Return value: **None**. It prints 0, 1, or 2 lines and never raises for normal inputs.

## HOW (integration points)
- Lazy imports **inside the helper** (consistent with existing lazy imports in this function):
  ```python
  from ...llm.providers.langchain import _load_langchain_config
  from ...llm.providers.langchain.verification import (
      _BACKEND_PACKAGES,
      _check_package_installed,
  )
  ```
- Uses existing module-level names already in `verify.py`: `_format_row`,
  `_VALUE_COLUMN_INDENT`, and `symbols["warning"]` (`[WARN]`).
- Wiring — change the `else` branch from:
  ```python
  else:
      print("  (uses Claude CLI — see Basic Verification above)")
  ```
  to:
  ```python
  else:
      print("  (uses Claude CLI — see Basic Verification above)")
      _print_langchain_readiness_warning(symbols)
  ```
- Do **not** touch `langchain_result` (stays `None` on this path), `_format_section`, or
  `_compute_exit_code`.

## ALGORITHM (core logic)
```
backend = _load_langchain_config().get("backend")
if not backend: return                      # not configured → note only
pkg = _BACKEND_PACKAGES.get(backend)
if pkg is None:                             # unrecognized backend name
    msg, hint = f"backend '{backend}' is not a recognized langchain backend", None
elif _check_package_installed(pkg): return  # installed → emit nothing new
else:                                        # known backend, module missing
    display = pkg.replace("_", "-")
    msg  = f"backend '{backend}' configured but {display} not installed"
    hint = f"pip install {display} (needed for --llm-method langchain)"
print(_format_row("Langchain backend", symbols["warning"], msg, indent=2))
if hint: print(f"{' ' * _VALUE_COLUMN_INDENT}-> {hint}")
```

## DATA
- `_BACKEND_PACKAGES` (existing, in `verification.py`): maps backend name →
  importable package, e.g. `{"anthropic": "langchain_anthropic", "openai": "langchain_openai",
  "gemini": "langchain_google_genai", "ollama": "langchain_ollama"}`.
- `_load_langchain_config()` returns a dict including key `"backend"` (str | None); reads via
  `get_config_values()` so `MCP_CODER_LLM_LANGCHAIN_BACKEND` counts as configured.
- Display name for messages/hints = `package.replace("_", "-")`.
- Output rows use `symbols["warning"] == "[WARN]"`; hint line is indented by
  `_VALUE_COLUMN_INDENT` and prefixed with `-> `.

---

## TDD — write these tests first, then implement

All three follow the pattern of `test_claude_fallback_note_when_claude_active`: patch
`resolve_llm_method` → `("claude", "default")`, `verify_claude` → ok, `verify_mlflow` →
not installed, `prompt_llm` → dummy response, and `log_to_mlflow`. Additionally patch the
langchain config + package check **at their source modules** (the helper imports them lazily):

- config: `patch("mcp_coder.llm.providers.langchain._load_langchain_config", ...)`
  returning `{"backend": <name>, ...}` (other keys may be `None`).
- package check: `patch(f"{_LC_VERIFY}._check_package_installed", return_value=<bool>)`.

Tests (all assert process **exit 0** — via `main()` returning 0 / no `SystemExit(1)`):

1. **`test_langchain_backend_warn_when_module_missing_claude_active`**
   backend `"anthropic"`, `_check_package_installed` → `False`.
   Assert output contains `"uses Claude CLI"` **and** `"[WARN]"` **and**
   `"backend 'anthropic' configured but langchain-anthropic not installed"` **and**
   `"-> pip install langchain-anthropic (needed for --llm-method langchain)"`.

2. **`test_langchain_backend_no_warn_when_module_installed_claude_active`**
   backend `"anthropic"`, `_check_package_installed` → `True`.
   Assert the **specific** langchain row is absent (a global `"[WARN]"`-absent
   assertion is unsafe — the redundancy note, MCP config warnings, and MCP
   "health check skipped" rows also emit `"[WARN]"` on the claude-active path).
   Assert `"uses Claude CLI"` present, and assert `"Langchain backend"` (the row
   label) **and** the message fragments `"configured but"` / `"not a recognized"`
   are **absent**. Do **not** assert `"[WARN]"` is absent globally.

3. **`test_langchain_backend_warn_when_unrecognized_backend_claude_active`**
   backend `"typo-backend"` (not in `_BACKEND_PACKAGES`); `_check_package_installed`
   need not be reached.
   Assert `"uses Claude CLI"` present, `"[WARN]"` present, and
   `"not a recognized langchain backend"` present. No `-> pip install` hint line.

Keep existing `test_claude_fallback_note_when_claude_active` behavior unchanged (note shown, no
warning) — it exercises the "not configured" path. Because the new helper now calls the real
`_load_langchain_config()` (reading the machine's real config) on every claude-active test, you
**must** patch `_load_langchain_config` → `{"backend": None}` for
`test_claude_fallback_note_when_claude_active` to keep it deterministic (otherwise a real
configured backend on the developer's machine would surface a warning and break the assertion).
The cleanest approach is a shared/autouse patch that also covers the other unpatched claude-active
tests in the file — e.g. `test_output_contains_status_symbols`,
`test_active_provider_shown_in_output`, and the claude cases in the exit-code matrix — so none of
them can be perturbed by the machine's real langchain config.

## Checks to run before committing (MCP tools, must all pass)
- `run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])`
- `run_pylint_check`
- `run_mypy_check`
- Format via `mcp__mcp-tools-py__run_format_code` before staging.

## Commit
Single commit containing the helper, the one-line wiring, and the three tests.
Suggested message:
`verify: warn on missing configured langchain backend module when claude active (#991)`

---

### LLM prompt for this step
> Implement Step 1 from `pr_info/steps/step_1.md`, using `pr_info/steps/summary.md` for the
> behavior matrix, sample output, and design rationale (readiness warning, exit 0, render inline,
> reuse existing helpers, build no result dict).
>
> Work test-first:
> 1. Add the three integration tests described under "TDD" to
>    `tests/cli/commands/test_verify_integration.py`, mirroring
>    `test_claude_fallback_note_when_claude_active`. Run them and confirm they fail.
> 2. Add `_print_langchain_readiness_warning(symbols)` to
>    `src/mcp_coder/cli/commands/verify.py` per the ALGORITHM, and call it in the `else`
>    branch of the `active_provider == "langchain"` gate right after the existing
>    `(uses Claude CLI …)` note. Reuse `_load_langchain_config`, `_BACKEND_PACKAGES`,
>    `_check_package_installed` via lazy imports; do NOT call `verify_langchain()`, do NOT
>    touch `_format_section`, `_compute_exit_code`, or `langchain_result`.
> 3. Run pytest (fast markers), pylint, and mypy via the MCP tools and fix everything until
>    all pass. Format the code. Produce exactly one commit.
>
> Use MCP tools exclusively for file and check operations, per `.claude/CLAUDE.md`.
