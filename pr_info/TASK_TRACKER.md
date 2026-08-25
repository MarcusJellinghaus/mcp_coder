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

---

## Tasks

### Step 1: Rename `endpoint` → `base_url`

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (All three ran; **zero findings in any file this step touches**. Step 1's own tests
      pass: `tests/utils/test_user_config_schema.py` + `tests/llm/providers/langchain/test_langchain_provider.py`
      → 43 passed. ruff clean; black 615 files unchanged; isort clean.
      Rename verified complete at every integration point in step_1.md §HOW:
      `user_config.py:57` (`base_url` + `MCP_CODER_LLM_LANGCHAIN_BASE_URL`), `__init__.py`
      141/149/163/192/218, both backend signatures (`ollama_backend.py:40` local correctly
      renamed to `resolved_url`), `_preflight.py:40`, `_errors_404.py:25,82`,
      `verification.py` (`_check_base_url_shape`, `error_type: "base_url"`), and all hint
      strings. Only `endpoint` spellings left in `src/`: the `endpoint_shape` key +
      `"Endpoint"` label (step 8), the `azure_endpoint=` SDK kwarg, and an unrelated
      `task_tracker.py` docstring — all intentional.)
- [x] Commit message prepared

### Step 2: Unknown-key hints: rename table + "did you mean"

Details: [step_2.md](./steps/step_2.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in any file this step touches**: pylint and mypy scoped to
      `src/mcp_coder/utils` + `tests/utils` are both clean; ruff clean; black/isort
      leave the files unchanged. Step 2's own tests pass — `tests/utils/test_config_hints.py`
      + `tests/utils/test_verify_config.py` → 31 passed; whole `tests/utils` → 309 passed;
      `tests/cli` → 1008 passed; `tests/llm` + `tests/config` + `tests/prompts` clean apart
      from the known environmental failures. lint-imports: 21 contracts kept.

      **Environment note (pytest again needs the shim).** The `.venv` copy of the
      unpinned git dependency `mcp-workspace` is stale once more: no
      `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via `mcp_coder/__init__.py:37`,
      so a bare `import mcp_coder` raises and **pytest collects zero tests** — the note
      dropped in `c1fae76` describes a real, still-present condition. Workaround used
      (no shell needed): a throwaway `.pytest_shim/sitecustomize.py` registering a
      stand-in `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus` from
      `mcp_workspace.checks.branch_status`, any str for `GITHUB_TOKEN_HINT`), run pytest
      with `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the directory afterwards —
      it is *not* committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all pre-existing:
      `tests/cli/commands/test_check_branch_status*.py` (stale `CIStatus.UNAVAILABLE` /
      `BranchStatusReport` API), `tests/llm/providers/copilot/test_copilot_integration.py`
      (no `copilot` CLI), `test_langchain_exceptions.py::...httpx_connect_error` (`httpx`
      absent → MagicMock). Project-wide pylint/mypy findings trace to the same causes and
      to the absent optional extras; none are in files this step touches.)
- [x] Commit message prepared

### Step 3: Warn on the retired `MCP_CODER_LLM_LANGCHAIN_ENDPOINT`

Details: [step_3.md](./steps/step_3.md)

- [x] Implementation (tests + production code)
      (`_RETIRED_ENV_VARS` table + `_print_retired_env_var_warning()` in
      `verify.py`, called at `execute_verify` step "0a" — right after the CONFIG
      loop and **outside both provider gates**, so langchain and claude users
      alike see it. Prints only; no result dict, so it cannot reach
      `_compute_exit_code`. Row passes `label_width=len(old)` because the
      32-char label overflows `_LABEL_WIDTH` (22). Same commit: corrected
      `_print_langchain_readiness_warning`'s docstring — it claimed "Runs
      regardless of active provider" while its only call site
      (`verify.py:470`) is the else-branch of the langchain gate.
      6 new tests in `tests/cli/commands/test_verify_orchestration.py`:
      langchain-active, claude-active, unset, exported-but-empty, the table
      mapping, and value-column alignment.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in either file this step touches**: pylint and mypy
      scoped to `verify.py` + `test_verify_orchestration.py` are both clean;
      ruff clean; black/isort leave both unchanged. Step 3's own module passes —
      `tests/cli/commands/test_verify_orchestration.py` → 25 passed;
      `tests/cli` → 1014 passed (step 2's 1008 + the 6 new tests).

      **Environment note — pytest still needs the shim.** Unchanged from step 2:
      the `.venv` copy of the unpinned git dependency `mcp-workspace` lacks
      `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and pytest
      collects zero tests. Same workaround: a throwaway `.pytest_shim/sitecustomize.py`
      registering a stand-in `mcp_workspace.checks.branch_status_rendering`
      (re-export `CIStatus` from `mcp_workspace.checks.branch_status`, any str
      for `GITHUB_TOKEN_HINT`), run pytest with
      `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the directory afterwards
      — it is **not** committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the four
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API) were excluded via
      `--ignore` for the 1014-test run; the only project-wide pylint (E1123) and
      mypy (`attr-defined`, `call-arg`) findings under `src/mcp_coder/cli` +
      `tests/cli` are the same four sites in `check_branch_status.py` /
      `test_check_branch_status_exit_code.py`.)
- [x] Commit message prepared

### Step 4: `_load_langchain_config()` must never raise

Details: [step_4.md](./steps/step_4.md)

- [x] Implementation (tests + production code)
      (`_load_langchain_config` now wraps `get_config_values` in
      `try/except ValueError`, logs a warning naming `[llm.langchain]` and
      pointing at the CONFIG section of `mcp-coder verify`, and falls back to
      `raw = {}`. Every field read switched from `raw[key]` to `raw.get(key)`
      so the empty-dict fallback degrades all six values to `None` via the
      unchanged `_str_or_none()` narrowing point. Signature and return shape
      untouched; **no validation added** (Decision 4 — that lands in step 5 at
      the point of use). Docstring restated as "Never raises" with the
      rationale. 3 new tests: the ValueError → all-None + warning case and a
      non-`str` value narrowing case in
      `tests/llm/providers/langchain/test_langchain_provider.py`, plus an
      end-to-end regression in `tests/cli/commands/test_verify_orchestration.py`
      driving `execute_verify` with a real `[llm.langchain] model = 123`
      through the claude path — it reaches the loader via
      `_print_langchain_readiness_warning` (`verify.py:470`) and now exits 1
      from the *config* error instead of tracebacking.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in either file this step touches**: pylint and mypy
      scoped to `llm/providers/langchain/__init__.py` +
      `test_langchain_provider.py` + `test_verify_orchestration.py` are both
      clean; ruff clean; black/isort leave all three unchanged. Step 4's own
      tests pass — the 8 tests of `TestLoadLangchainConfig` +
      `TestVerifySurvivesMistypedLangchainConfig` (2 failing before the change,
      for exactly the intended reason: the `ValueError` escaping through
      `verify.py:470` → `_print_langchain_readiness_warning` →
      `_load_langchain_config`). Wider runs: `tests/cli` → 992 passed,
      `tests/llm` + `tests/utils` clean apart from the known environmental
      failures.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-3: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and
      pytest collects zero tests. Same workaround: a throwaway
      `.pytest_shim/sitecustomize.py` registering a stand-in
      `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus` from
      `mcp_workspace.checks.branch_status`, any str for `GITHUB_TOKEN_HINT`),
      run pytest with `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the
      directory afterwards — it is **not** committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches. The `check_branch_status`
      family is now **six** modules, not the four excluded in step 3:
      `test_check_branch_status_ci_waiting.py` and
      `test_check_branch_status_pr_waiting.py` join it (8 further failures, all
      `assert 2 == 0`). Root cause traced this run and identical to the other
      four: `checks/ci_policy.py:42` reads `CIStatus.UNAVAILABLE`, absent from
      the stale enum, so the `AttributeError` hits the broad
      `except Exception -> return 2` in `execute_check_branch_status`. Verified
      independent of this step — `check_branch_status.py` contains no
      `langchain` or `get_config_values` reference at all. `--ignore-glob=**/test_check_branch_status*.py`
      gives the 992-test `tests/cli` run. Also environmental: the three
      `tests/llm/providers/copilot/test_copilot_integration.py` tests (no
      `copilot` CLI) and `test_langchain_exceptions.py::...httpx_connect_error`
      (`httpx` absent → MagicMock). Project-wide mypy over `src/mcp_coder/llm` +
      `src/mcp_coder/cli` reports exactly the 3 known `check_branch_status.py`
      findings (1 `attr-defined`, 2 `call-arg`); the langchain-package pylint
      run reports only `E0401` for the uninstalled optional extras.)
- [x] Commit message prepared

### Step 5: Per-backend contract validator (Azure rule included)

Details: [step_5.md](./steps/step_5.md)

- [x] Implementation (tests + production code)
      (New `llm/providers/langchain/_config_diagnostics.py`: `Status`,
      `_CONTRACT` (5 mode rows), `_SUPPORTED_BACKENDS`, `_API_KEY_ENV`,
      `_KEYLESS_ENV`, `_API_KEY_SUFFIX`, the `Finding` TypedDict, `mode_of()`
      and a pure, non-raising `validate()`. **Everything is keyed by the
      *mode*** — `_API_KEY_ENV` carries its own `"azure"` row, so an Azure
      config whose key comes from `OPENAI_API_KEY` produces no finding
      (Decision 6). Rows are tuples covering every variable the SDKs actually
      read: azure also `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_AD_TOKEN`
      (resolved by `openai.AzureOpenAI` itself, since `create_openai_model`
      passes `api_key=None` through), gemini also `GOOGLE_API_KEY` (langchain's
      `secret_from_env([...])` factory). `_KEYLESS_ENV` adds gemini/Vertex as
      the one credential-free carve-out, tested for **presence** not
      truthiness. `openai`/`azure` `api_key` is unconditionally `ok=False` —
      no `base_url` exception (Decision 5 is contradicted by the installed
      SDK). One conditional rule: azure `base_url` is satisfied by config
      **or** `AZURE_OPENAI_ENDPOINT`, read straight from `os.environ` because
      the explicit `azure_endpoint=None` bypasses langchain's `from_env`
      factory. `mode_of()` returns `None` for a literal `backend = "azure"`,
      whose finding reproduces the existing `Unsupported langchain backend`
      wording verbatim. Wired into `_create_chat_model` as three lines
      **before** the dispatch, so all four provider paths (text, text-stream,
      agent, agent-stream) are covered by one site; module-level
      `from ._config_diagnostics import validate` is safe because
      `_config_diagnostics` imports stdlib only (the cycle guard step 6
      depends on). 38 table-driven tests in new
      `tests/llm/providers/langchain/test_langchain_contract.py`, covering
      every TDD case 1-8 including 4b/4c/4d, 5b and 7b; 4c and 5b also call
      the real `create_openai_model` / `create_gemini_model` so the widened
      env rows cannot silently drift from the SDKs' own fallback chains.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in either file this step touches**: pylint scoped to
      `_config_diagnostics.py` + `test_langchain_contract.py` reports nothing;
      mypy over `src/mcp_coder/llm/providers/langchain` +
      `tests/llm/providers/langchain` is clean; ruff clean; isort clean; black
      reformatted the new test file once and is now a no-op. lint-imports:
      21 contracts kept. Step 5's own tests pass — `test_langchain_contract.py`
      → 38 passed. Wider runs: `tests/cli` + `tests/utils` → 1301 passed;
      `tests/llm` clean apart from the known environmental failures below.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-4: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and
      pytest collects zero tests. Same workaround: a throwaway
      `.pytest_shim/sitecustomize.py` registering a stand-in
      `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus`
      from `mcp_workspace.checks.branch_status`, any str for
      `GITHUB_TOKEN_HINT`), run pytest with
      `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the directory
      afterwards — it is **not** committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the six
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API), excluded via
      `--ignore-glob` for the 1301-test run; the three
      `tests/llm/providers/copilot/test_copilot_integration.py` tests (no
      `copilot` CLI); and
      `test_langchain_exceptions.py::...httpx_connect_error` (`httpx` absent →
      MagicMock). The only project-wide pylint findings under the langchain
      package are `E0401` for the uninstalled optional extras
      (`langchain_core`, `langchain_openai`, `httpx`, …) — which also means
      the two SDK-construction guards in 4c/5b pass trivially here and only
      bite in CI where the extras are installed.

      **Pre-existing file-size violation, out of scope for this step:**
      `mcp-coder check file-size --max-lines 750` flags
      `tests/cli/commands/test_verify_orchestration.py` at 871 lines (grown by
      steps 3 and 4). Step 5 does not touch that file.)
- [x] Commit message prepared

### Step 6: `resolve_target()`: read the dialed URL off the constructed client

Details: [step_6.md](./steps/step_6.md)

- [x] Implementation (tests + production code)
      (`_config_diagnostics.py` gains `ResolvedTarget` (frozen slots
      dataclass), `dialed_url()`, `resolve_target()`,
      `redirect_env_in_effect()`, `_targets_match()` and the `_REDIRECT_ENV`
      table, plus the `_UNSET_TARGET` / `_NO_BACKEND_TARGET` /
      `_UNKNOWN_TARGET` / `_OLLAMA_DEFAULT_URL` constants. The URL is read off
      a locally constructed client — `root_client.base_url` (ChatOpenAI /
      AzureChatOpenAI, stringified because the SDK exposes an `httpx.URL`)
      then `base_url` (ChatOllama) — never computed from config. `mode_of()`
      gates *before* the `("openai", "ollama")` test so an unset or typo'd
      backend gets `(backend not configured)` / `"no supported backend
      configured"` with `verified=False` rather than the gemini/anthropic
      "no configurable target" claim. Construction failure names `config.toml`
      only when a config `base_url` actually supplied the fallback value.
      Provenance needs **both** filters: mode-applicability
      (`AZURE_OPENAI_ENDPOINT` in Azure mode only) and a value match against
      the dialed URL, so a stale exported variable is inert; tuple order
      (`OPENAI_API_BASE` first) breaks the same-value tie. A constructed
      ollama client reporting `base_url = None` falls back to
      `_resolve_ollama_host(...) or http://localhost:11434`, never
      `(unknown)`. Both httpx clients are closed in a `finally`.
      `_create_chat_model`'s `config` parameter widened
      `dict` → `Mapping[str, str | None]` (`__init__.py:186`, `Mapping` added
      to the `collections.abc` import); all four call sites pass dicts and are
      unchanged. 31 tests in new
      `tests/llm/providers/langchain/test_langchain_resolve_target.py` covering
      TDD cases 1-8 including 2b/2c/3b/3c/4b/5b/7b, driven by a stub chat model
      so no langchain install is needed.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in either file this step touches**: mypy over
      `src/mcp_coder/llm/providers/langchain` + `tests/llm/providers/langchain`
      is clean; pylint over the same package (minus the `E0401` extras noise)
      reports nothing; ruff `--preview` clean; black/isort leave both files
      unchanged after one reformat. lint-imports: 21 contracts kept. Step 6's
      own tests pass — `test_langchain_resolve_target.py` → 31 passed. Wider
      runs: `tests/cli` + `tests/utils` → 1301 passed; `tests/llm` clean apart
      from the known environmental failures below.

      **One finding was real and is fixed:** pylint has `R0401` explicitly
      enabled, and the mandated deferred `from . import _create_chat_model`
      makes the package↔module cycle visible to it even though it never
      executes at import time. Suppressed at the import line with
      `# pylint: disable=cyclic-import`, the same convention
      `claude_code_cli.py:406` already uses for its deferred import. The cycle
      *is* only deferred, not absent — hence TDD case 8, which drops every
      `mcp_coder.llm.providers.langchain*` entry from `sys.modules` and
      re-imports the package from scratch.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-5: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and
      pytest collects zero tests (confirmed again this run: the first
      unshimmed run collected 0). Same workaround: a throwaway
      `.pytest_shim/sitecustomize.py` registering a stand-in
      `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus`
      from `mcp_workspace.checks.branch_status`, any str for
      `GITHUB_TOKEN_HINT`), run pytest with
      `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the directory
      afterwards — it is **not** committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the six
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API), excluded via
      `--ignore-glob` for the 1301-test run; the three
      `tests/llm/providers/copilot/test_copilot_integration.py` tests (no
      `copilot` CLI); and
      `test_langchain_exceptions.py::...httpx_connect_error` (`httpx` absent →
      MagicMock). Because the extras are absent, the stub-driven design of the
      new tests is what makes step 6 testable here at all.

      **Pre-existing file-size violation, out of scope for this step:**
      `mcp-coder check file-size --max-lines 750` still flags only
      `tests/cli/commands/test_verify_orchestration.py` at 871 lines, grown by
      steps 3 and 4. Step 6 does not touch that file;
      `_config_diagnostics.py` is at 500 lines.)
- [x] Commit message prepared

### Step 7: Effective-config echo + env-redirection flag + api_key override flag

Details: [step_7.md](./steps/step_7.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Rebase the base-URL shape check on the resolved target

Details: [step_8.md](./steps/step_8.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 9: Contract findings in `verify` + exit-code wiring

Details: [step_9.md](./steps/step_9.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 10: Connection errors name the host actually dialed

Details: [step_10.md](./steps/step_10.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 11: `--check-models` cross-checks the configured model

Details: [step_11.md](./steps/step_11.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 12: `prompt_llm` / `prompt_llm_stream` honour their `provider=` argument

Details: [step_12.md](./steps/step_12.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 13: `verify`'s test prompt carries the real message shape

Details: [step_13.md](./steps/step_13.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 14: Surface `MCP_CODER_LLM_PROVIDER` in `verify`

Details: [step_14.md](./steps/step_14.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 15: Prompt path resolver + runtime WARNING on a missing configured prompt

Details: [step_15.md](./steps/step_15.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 16: PROMPTS section: lengths, and configured-but-missing → error

Details: [step_16.md](./steps/step_16.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 17: TLS / proxy summary line

Details: [step_17.md](./steps/step_17.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 18: Smart-quote hint in `_format_toml_error`

Details: [step_18.md](./steps/step_18.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 19: Documentation

Details: [step_19.md](./steps/step_19.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review
- [ ] PR summary
