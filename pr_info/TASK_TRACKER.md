# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

**Note scope:** keep per-step notes to a line or two. The design rationale
lives in `steps/step_N.md` and the per-step commit messages; the recurring
environment caveats are recorded once under
[Environment notes](#environment-notes) rather than repeated per step.

---

## Tasks

### Step 1: Rename `endpoint` → `base_url`

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
      (Rename applied at every integration point listed in step_1.md §HOW. The
      only `endpoint` spellings left in `src/` are intentional: the
      `endpoint_shape` key + `"Endpoint"` label — both retired in step 8 — and
      the `azure_endpoint=` SDK kwarg.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; step's own tests → 43 passed.)
- [x] Commit message prepared

### Step 2: Unknown-key hints: rename table + "did you mean"

Details: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; `tests/utils/test_config_hints.py` + `test_verify_config.py` →
      31 passed, `tests/utils` → 309, `tests/cli` → 1008.)
- [x] Commit message prepared

### Step 3: Warn on the retired `MCP_CODER_LLM_LANGCHAIN_ENDPOINT`

Details: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
      (`_RETIRED_ENV_VARS` table + `_print_retired_env_var_warning()`, called at
      `execute_verify` step "0a" — **outside both provider gates**, prints only,
      so it cannot reach `_compute_exit_code`. Same commit corrected
      `_print_langchain_readiness_warning`'s docstring, which claimed to run
      regardless of provider. 6 new tests.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; `tests/cli` → 1014 passed.)
- [x] Commit message prepared

### Step 4: `_load_langchain_config()` must never raise

Details: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
      (`get_config_values` wrapped in `try/except ValueError` → warning + `raw =
      {}` fallback; every field read switched to `raw.get(key)`. No validation
      added — that is step 5 (Decision 4). 3 new tests, incl. an end-to-end
      regression driving `execute_verify` with `[llm.langchain] model = 123`.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; `tests/cli` → 992 passed.)
- [x] Commit message prepared

### Step 5: Per-backend contract validator (Azure rule included)

Details: [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
      (New `llm/providers/langchain/_config_diagnostics.py` — stdlib-only, so
      the module-level import into `_create_chat_model` stays cycle-free.
      Everything is keyed by the **mode**, not the backend (Decision 6), and
      `validate()` is pure and non-raising. 38 table-driven tests in new
      `test_langchain_contract.py`.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; 38 passed, `tests/cli` + `tests/utils` → 1301.)
- [x] Commit message prepared

### Step 6: `resolve_target()`: read the dialed URL off the constructed client

Details: [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code)
      (`ResolvedTarget` / `dialed_url()` / `resolve_target()` /
      `redirect_env_in_effect()`. The URL is read off a locally constructed
      client, never computed from config; provenance needs both a
      mode-applicability and a value match, so a stale exported variable is
      inert. `_create_chat_model`'s `config` widened to
      `Mapping[str, str | None]`. 31 stub-driven tests.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (One real finding fixed: pylint `R0401` sees the deferred
      `from . import _create_chat_model` cycle — suppressed at the import line
      with `# pylint: disable=cyclic-import`, the convention
      `claude_code_cli.py:406` already uses. 31 passed.)
- [x] Commit message prepared

### Step 7: Effective-config echo + env-redirection flag + api_key override flag

Details: [step_7.md](./steps/step_7.md)

- [x] Implementation (tests + production code)
      (`describe_effective_config()` is pure formatting — the masked key, its
      source and the override flag all arrive from the one `_resolve_api_key`
      call. `_BACKEND_ENV_VARS` deleted; `_resolve_api_key` re-keyed on the mode
      and returning `(key, source, overridden)`, resolving in the order the
      *client* resolves. `verify.py` only prints. 25 new tests; the
      `_resolve_api_key` tests moved into new
      `test_langchain_effective_config.py`.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; 164 + 21 passed.)
- [x] Commit message prepared

### Step 8: Rebase the base-URL shape check on the resolved target

Details: [step_8.md](./steps/step_8.md)

- [x] Implementation (tests + production code)
      (`_check_base_url_shape` takes step 7's `ResolvedTarget` — no second
      resolution, no second chat-model construction. Heuristics byte-identical;
      sentinels imported rather than re-typed. Carries Decision 19's deferred
      half: `endpoint_shape` → `base_url_shape`, `"Endpoint"` → `"Base URL"`.
      29 tests in new `test_langchain_base_url_shape.py` — split out rather
      than appended, to keep `test_langchain_verification.py` under 750.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; 29 passed, `tests/cli` → 996.)
- [x] Commit message prepared

### Step 9: Contract findings in `verify` + exit-code wiring

Details: [step_9.md](./steps/step_9.md)

- [x] Implementation (tests + production code)
      (`verify_langchain` calls `validate()` once and merges the findings;
      defaults are contract-aware, so a typo'd backend never renders
      `Model [OK] None`. `overall_ok` gains the findings check — errors exit 1,
      `ok=None` warnings stay neutral — and `verify_exit_code.py` is untouched
      as specified. 20 tests in new `test_langchain_contract_rows.py` + the
      exit-code case in `test_verify_exit_codes.py`. Two existing tests changed
      because step 9 deliberately changes their subject.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean.)
- [x] Commit message prepared

### Step 10: Connection errors name the host actually dialed

Details: [step_10.md](./steps/step_10.md)

- [x] Implementation (tests + production code)
      (`_handle_provider_error` gains `dialed`, threaded through all four
      provider call sites with `dialed_url(chat_model)`; the falsy guard keeps
      `dialed=""` on the static hint. `_list_models_for_backend` appends
      `— tried {base_url}` only when a base_url was actually handed to the SDK.
      17 tests in new `test_langchain_dialed_host.py`.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean.)
- [x] Commit message prepared

### Step 11: `--check-models` cross-checks the configured model

Details: [step_11.md](./steps/step_11.md)

- [x] Implementation (tests + production code)
      (`_check_model_listed()` rides on the listing `--check-models` already
      fetched — no second network call — and near-misses reuse step 2's
      `suggest()`. Advisory by construction: `ok` is only `True` or `None` and
      the call sits below `overall_ok`'s inputs, so `verify_exit_code.py` is
      untouched. 13 tests appended to `test_langchain_verification.py`.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean.)
- [x] Commit message prepared

### Step 12: `prompt_llm` / `prompt_llm_stream` honour their `provider=` argument

Details: [step_12.md](./steps/step_12.md)

- [x] Implementation (tests + production code)
      (Both signatures become `provider: str | None = None`, resolving
      `provider or env or "claude"`, so an explicit provider always wins; the
      unsupported-provider `ValueError` stays after resolution.
      `cli/utils.resolve_llm_method` still owns the config tier, so no
      `llm → cli` import. All 22 in-repo call sites already pass `provider=`.
      4 red → 9 green.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean.)
- [x] Commit message prepared

### Step 13: `verify`'s test prompt carries the real message shape

Details: [step_13.md](./steps/step_13.md)

- [x] Implementation (tests + production code)
      (One kwarg — `project_dir=` on the `"Reply with OK"` call — which is what
      makes `prompt_llm` run `load_prompts` instead of handing the provider
      `system_prompt=None`. No new flag, no per-provider conditional; the smoke
      test is untouched. New `TestVerifyTestPromptCarriesProjectDir`,
      3 red → 4 green.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; 30 passed in the module.)
- [x] Commit message prepared

### Step 14: Surface `MCP_CODER_LLM_PROVIDER` in `verify`

Details: [step_14.md](./steps/step_14.md)

- [x] Implementation (tests + production code)
      (Twelve lines beside the `Active provider` row plus `_PROVIDER_ENV_VAR` /
      `_PROVIDER_ENV_SOURCE`. The row prints only when the var is set AND did
      not decide the provider; it touches no result dict, so it is
      exit-neutral. New `TestProviderEnvVarVisibility`, 2 red → 4 green.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; 25 passed in the module.)
- [x] Commit message prepared

### Step 15: Prompt path resolver + runtime WARNING on a missing configured prompt

Details: [step_15.md](./steps/step_15.md)

- [x] Implementation (tests + production code)
      (Duplicated absolute/relative resolution extracted into `_resolve_path()`,
      now the single implementation behind `_resolve_and_read`,
      `get_project_prompt_path` and the new
      `is_prompt_configured_but_missing()`. A missing *configured* path logs one
      deduped WARNING and still returns `None`, so the shipped-default fallback
      is untouched and nothing raises (Decision 8). 14 new tests + an autouse
      cache-clearing fixture so counts survive `-n auto`.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; `tests/prompts` 22 → 36 passed.)
- [x] Commit message prepared

### Step 16: PROMPTS section: lengths, and configured-but-missing → error

Details: [step_16.md](./steps/step_16.md)

- [x] Implementation (tests + production code)
      (The two prompt rows became a loop driven by step 15's predicate:
      configured-and-missing → `[ERR]` + `prompts_ok = False`, every other case
      keeps `[OK]` and gains `({len} chars)` from the content `load_prompts`
      already returned — no second read. `_compute_exit_code` gains
      `prompts_ok`. 9 new tests, 5 of them in new
      `test_verify_prompts_section.py` — a new file because appending to
      `test_verify_sections_orchestration.py` would have broken the size gate.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean.)
- [x] Commit message prepared

### Step 17: TLS / proxy summary line

Details: [step_17.md](./steps/step_17.md)

- [x] Implementation (tests + production code)
      (`_print_environment_section` lazily imports `_truststore_available` /
      `_proxy_configured` from `_exceptions` — no new helper and no new
      import-graph edge — and prints one marker-free `TLS / proxy` row. Only
      the boolean proxy state is rendered; the URL never reaches stdout.
      `TestTlsProxySummaryRow`, 10 tests incl. the credential-leak assertion,
      red before the production edit.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; `tests/cli` → 1115 passed.)
- [x] Commit message prepared

### Step 18: Smart-quote hint in `_format_toml_error`

Details: [step_18.md](./steps/step_18.md)

- [x] Implementation (tests + production code)
      (`error_line` hoisted out of the `try` block, so the existing `OSError`
      path yields no hint, and a second `Hint:` block appended beside the
      backslash one. No signature change, no second file read; new
      `_SMART_QUOTES` constant. 5 new tests, red first.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (Clean; `tests/utils` → 314 passed.)
- [x] Commit message prepared

### Step 19: Documentation

Details: [step_19.md](./steps/step_19.md)

- [x] Implementation (tests + production code)
      (Docs only. `docs/configuration/config.md`: `base_url` documented with a
      rename/migration note, a new scenario→values table, a
      "variables that change behaviour invisibly" table and a LangChain
      symptom → cause troubleshooting subsection; all TOML examples switched to
      `base_url`. `docs/architecture/architecture.md` lists
      `_config_diagnostics.py`. The scenario table was read side by side with
      `_CONTRACT` and agrees cell for cell.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (No Python touched, so no new findings are possible — and none appeared.)
- [x] Commit message prepared

---

## Environment notes

Recorded once instead of per step. All of these are pre-existing, environmental
and unrelated to any step above.

- **`mcp-workspace` is stale in the venv.** The installed copy of the unpinned
  git dependency predates `mcp_workspace.checks.branch_status_rendering`, which
  `src/mcp_coder/checks/branch_status.py:17` imports via
  `mcp_coder/__init__.py:37` — so a bare `import mcp_coder` raises and pytest
  collects **zero** tests. Workaround used throughout: a throwaway
  `.pytest_shim/sitecustomize.py` registering a stand-in module, run pytest with
  `env_vars={"PYTHONPATH": ".pytest_shim"}`, then delete the directory — it is
  **not** committed. Real fix needs a shell:
  `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
  then `pip install -e ".[langchain]"`.
- **Known-failing baseline.** The same staleness is the sole source of the
  `tests/cli/commands/test_check_branch_status*.py` and
  `tests/workflows/review/test_*gates.py` failures (`CIStatus.UNAVAILABLE` /
  `CIStatus.UNKNOWN` / `BranchStatusReport` API drift) and of the project-wide
  mypy `attr-defined` / `call-arg` and pylint `E1123` findings in
  `check_branch_status.py`. Missing optional packages account for the rest:
  `tests/llm/providers/copilot/test_copilot_integration.py` (no `copilot` CLI),
  `test_langchain_exceptions.py::…httpx_connect_error` (no `httpx`),
  `tests/icoder/test_snapshots.py` (no `pytest-textual-snapshot`), and the
  pylint `E0401` noise for the uninstalled `langchain_*` extras.

---

## Pull Request

- [ ] PR review
- [ ] PR summary
