# Summary — Issue #991: readiness warning for configured langchain backend module when claude is active

## Goal
`mcp-coder verify` should warn (never fail) when `[llm.langchain] backend` is configured
but its optional backend module is missing — **regardless of the active provider**. Today
this check only runs when langchain is the *active* provider. When Claude is active, langchain
is still reachable on demand (`--llm-method langchain`, `MCP_CODER_LLM_PROVIDER`, or the default),
so a missing module is a **readiness** gap worth a quiet `[WARN]` (exit 0), not an error.

## Behavior matrix (target)
| Active provider | Backend config | Result |
|---|---|---|
| claude (langchain idle) | known backend, module **missing** | `(uses Claude CLI …)` note **kept** + `[WARN]` row + install hint, **exit 0** |
| claude (langchain idle) | known backend, module installed | note only — no warning |
| claude (langchain idle) | **unrecognized** backend name | note kept + `[WARN]` "not a recognized langchain backend", **exit 0** |
| claude (langchain idle) | not configured | note only (unchanged) |
| langchain | module missing / unknown backend | `[ERR]` + exit 1 (unchanged) |
| langchain | installed | `[OK]` (unchanged) |

### Sample output (claude active, backend `anthropic`, module missing)
```
=== LLM PROVIDER ==========================================================
  Active provider          [OK]   claude (from default)
  (uses Claude CLI — see Basic Verification above)
  Langchain backend        [WARN] backend 'anthropic' configured but langchain-anthropic not installed
                              -> pip install langchain-anthropic (needed for --llm-method langchain)
```

## Architectural / design changes
This is a **small, localized behavior addition** — no new modules, no new abstractions,
no signature changes to existing public functions.

- **One new private helper** in `verify.py`: `_print_langchain_readiness_warning(symbols)`.
  It loads langchain config, checks the configured backend's module, and prints an inline
  `[WARN]` row (+ install hint) only when there is a gap. It **returns nothing and builds no
  result dict**.
- **The `else` branch** of the `active_provider == "langchain"` gate (verify.py ~778-779)
  gains one call to that helper, after the existing `(uses Claude CLI …)` note (which stays).
- **Exit-code safety is structural, not bookkeeping.** Because the helper only *prints* and
  never produces a result dict, `langchain_result` stays `None` on the claude path and can
  never reach `_compute_exit_code`. There is no "separate variable" to manage — the KISS win
  is that exit safety is impossible to break here.
- **Reuse, don't reimplement.** The helper imports the three existing helpers from
  `langchain/verification.py` / `langchain/__init__.py`:
  `_load_langchain_config()`, `_BACKEND_PACKAGES`, `_check_package_installed()`.
  It does **not** call `verify_langchain()` (which also does API-key resolution and, for
  ollama, a live daemon probe — none of which belong on the idle readiness path).
- **Render inline, not via `_format_section`.** `_format_section` only emits `install_hint`
  when `ok is False`, never for the `ok=None` (⚠) case — it would silently drop the hint.
  The helper builds the row with `_format_row(..., symbols["warning"], ...)` and prints the
  `-> …` hint as an explicit follow-up line. The shared `_format_section` (line-370 gate) is
  left untouched.

### Design rationale (readiness, not consistency)
The message says *the module needed to use langchain isn't installed* — NOT that the config
is wrong. claude-default + langchain-provisioned is a **valid, common** state
(`resolve_llm_method` treats `default_provider` as only the default; langchain still runs when
selected explicitly or via env). So: WARN + exit 0, and only when there's an actual gap
(known backend + installed → emit nothing new).

### Scope discipline
Only the configured **backend module** is checked. `langgraph` / `langchain-mcp-adapters` are
NOT added to this idle-path check (not individually configured, not required for a claude run).
The pre-existing "MCP SERVERS (… for completeness)" section is untouched. Git verification is
already complete — out of scope.

## Folders / modules / files created or modified
**Modified**
- `src/mcp_coder/cli/commands/verify.py`
  - add `_print_langchain_readiness_warning(symbols: dict[str, str]) -> None`
  - call it in the `else` branch after the `(uses Claude CLI …)` note (~line 779)
- `tests/cli/commands/test_verify_integration.py`
  - add 3 integration tests (missing module, installed module, unrecognized backend)
  - existing `test_claude_fallback_note_when_claude_active` stays valid

**Created**
- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md`

**Unchanged (intentionally)**
- `src/mcp_coder/llm/providers/langchain/verification.py` — helpers reused as-is, no edits.
- `_format_section` / `_compute_exit_code` — untouched.

## Steps
- **Step 1** — Add the readiness-warning helper, wire it into the `else` branch, and cover all
  claude-active cases with tests. Single commit (TDD: tests + implementation + checks).
