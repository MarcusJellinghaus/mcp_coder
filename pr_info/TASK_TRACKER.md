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

- [x] Implementation (tests + production code)
      (`_config_diagnostics.py` gains `describe_effective_config()` plus the
      `_describe_mode` / `_describe_api_key` helpers and the `_NOT_CONFIGURED`
      / `_NO_MODE` constants. The builder is **pure formatting**: it never calls
      `resolve_target`, never masks, and never reads `config["api_key"]` — the
      masked value, its source and the override flag all arrive from the one
      `_resolve_api_key` call, so a row can never show one source's value under
      another's label. The `mode` row is guarded on `mode_of(config) is None`
      (`(not applicable — backend not configured)`, never
      `plain None (…)`), and the non-Azure parenthetical is derived from the
      config so a `gemini` config with a stray `api_version` reads
      `plain gemini (api_version ignored by gemini)` instead of contradicting
      step 9's `[WARN] … ignored` row.

      `verification.py`: `_BACKEND_ENV_VARS` **deleted**; `_resolve_api_key` is
      re-keyed on the *mode* (importing `_API_KEY_ENV`, `_KEYLESS_ENV`,
      `mode_of` from `_config_diagnostics`) and returns
      `(key, source, overridden)`. It resolves in the order the *client*
      resolves — `_API_KEY_ENV[mode][0]` (the only variable our own
      `create_*_model` reads, and it beats config) > config `api_key` > the
      row's remaining variables (SDK fallbacks, reached only when no key is
      passed at all) > `_KEYLESS_ENV` — so an Azure key in
      `AZURE_OPENAI_API_KEY` is *named* rather than rendered `(not set)`, while
      a configured key with only a secondary variable exported still reports
      `config.toml`. `overridden` is set **only** in the primary-beats-config
      case. `verify_langchain` makes the single `resolve_target(config)` call of
      the run and shares the `ResolvedTarget`; the rows land in the
      list-valued `result["effective_config"]`, which `_format_section`,
      `_collect_install_hints` and `_compute_exit_code` all skip by their
      existing isinstance guards. The `base_url_redirect` row is keyed on
      `redirect_env_in_effect(config, target.url)` and suppressed via step 6's
      `_targets_match` when config already implied that URL, so a stale
      `AZURE_OPENAI_ENDPOINT` or a losing `OPENAI_BASE_URL` produces no row;
      `api_key_override` is built from `key_source` and gated on
      `key_overridden`, never from the `env_var` local. Two `_LABEL_MAP`
      entries added. `verify.py` only *prints*, under its own
      `EFFECTIVE CONFIG` header with an empty marker
      (`_format_row(label, "", value, indent=2)`), guarded on the key being
      present so mocked results without it render unchanged.

      Tests: 21 builder tests in `test_langchain_resolve_target.py` (TDD 1, 2,
      3, 3b) and 4 rendering tests in `test_verify_sections_orchestration.py`
      (TDD 5, plus the two flag rows' `[WARN]` markers). The `_resolve_api_key`
      tests moved out of `test_langchain_verification.py` (661 lines — updating
      in place would have pushed it past the 750-line limit) into the new
      `test_langchain_effective_config.py`, rewritten for the 3-tuple and
      extended with TDD 3c/3d, alongside the `verify_langchain` wiring tests for
      TDD 4, 6, 6b and 7.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in any file this step touches**: pylint scoped to the
      six touched source/test files reports nothing; mypy over
      `src/mcp_coder/llm/providers/langchain`, `tests/llm/providers/langchain`,
      `verify.py`, `verify_formatting.py` and
      `test_verify_sections_orchestration.py` is clean; ruff clean; isort
      clean; black reformatted four files once and is now a no-op across 621
      files. lint-imports: 21 contracts kept. Step 7's own tests pass —
      `test_langchain_resolve_target.py` + `test_langchain_effective_config.py`
      + `test_langchain_verification.py` + `test_langchain_contract.py` →
      164 passed; `test_verify_sections_orchestration.py` → 21 passed. Wider
      run: all of `tests/llm/providers/langchain` plus the four verify CLI
      modules → clean apart from the one known environmental failure below.
      `mcp-coder check file-size --max-lines 750` flags only the pre-existing
      `tests/cli/commands/test_verify_orchestration.py` (871 lines, grown by
      steps 3-4); step 7 does not touch it. `_config_diagnostics.py` is at 597
      lines.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-6: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and
      pytest collects zero tests (confirmed again this run: the first
      unshimmed run collected 0). Same workaround: a throwaway
      `.pytest_shim/sitecustomize.py` registering a stand-in
      `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus` from
      `mcp_workspace.checks.branch_status`, any str for `GITHUB_TOKEN_HINT`),
      run pytest with `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the
      directory afterwards — it is **not** committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the six
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API), excluded via
      `--ignore-glob` for the `tests/cli` + `tests/llm` run; the three
      `tests/llm/providers/copilot/test_copilot_integration.py` tests (no
      working `copilot` CLI); and
      `test_langchain_exceptions.py::…httpx_connect_error` (`httpx` absent →
      MagicMock). Project-wide mypy over `src/mcp_coder/cli/commands` reports
      exactly the 4 known `check_branch_status` findings; the langchain-package
      pylint run reports only `E0401` for the uninstalled optional extras.)
- [x] Commit message prepared

### Step 8: Rebase the base-URL shape check on the resolved target

Details: [step_8.md](./steps/step_8.md)

- [x] Implementation (tests + production code)
      (`_check_base_url_shape` now takes the `ResolvedTarget` step 7 binds from
      the run's single `resolve_target(config)` call — no second resolution and
      no second chat-model construction. The three heuristics are byte-identical;
      only the input changed, plus a `(source: {target.source})` suffix on **all
      four** returned values. Skips: `api_version` (explicit Azure skip — the
      resolved Azure URL ends in `openai/deployments/<name>/`, so the `/v1` rule
      would fire on a correct config) and both sentinels, `"n/a"` and
      `_UNSET_TARGET` **imported** from `_config_diagnostics` rather than
      re-typed, so the sentinel can never be reported as a malformed URL; a
      *configured* `base_url` is still checked in the unverified case. Call-site
      gate unchanged at `backend == "openai"` — `/v1` is an OpenAI/relay
      convention and a correct ollama host has none, so an `OLLAMA_HOST` redirect
      is left to the `base_url_redirect` row. Still advisory: `ok` is only True
      or None, never False. Same commit carries Decision 19's deferred half —
      result key `endpoint_shape` → `base_url_shape` and `_LABEL_MAP`
      `"Endpoint"` → `"Base URL"`.

      **Test placement note.** The shape tests live in the new
      `tests/llm/providers/langchain/test_langchain_base_url_shape.py` (29 tests,
      TDD cases 1-9) rather than being added to `test_langchain_verification.py`
      as step_8.md's WHERE suggests: that file is at 614 lines, the new coverage
      is ~180, and step 9 adds contract rows to the same file — in-place would
      have pushed it against the 750-line limit, the same reasoning step 7 used
      when it split `test_langchain_effective_config.py` out. The old
      config-string tests (`TestCheckBaseUrlShape`,
      `TestVerifyLangchainEndpointShape`) are deleted from
      `test_langchain_verification.py`. The `verify_langchain` wiring tests stub
      `_create_chat_model` so the **real** `resolve_target` runs end to end
      without a langchain install; TDD 8 instead patches `resolve_target` itself
      and asserts `call_count == 1` with both the echo and the shape row present.
      TDD 9 asserts `_LABEL_MAP["base_url_shape"] == "Base URL"` and that no
      `"Endpoint"` label survives anywhere in the map.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in any file this step touches**: pylint scoped to
      `verification.py`, `verify_formatting.py` and the three touched test files
      reports nothing beyond the environmental `E0401`; mypy over
      `src/mcp_coder/llm/providers/langchain`, `src/mcp_coder/cli/commands`,
      `tests/llm/providers/langchain` and `tests/cli/commands` reports only the
      4 known `check_branch_status` findings; ruff clean; isort clean; black
      reformatted the new test file once and is now a no-op across 622 files.
      lint-imports: 21 contracts kept. Step 8's own tests pass —
      `test_langchain_base_url_shape.py` → 29 passed. Wider runs: `tests/cli`
      → 996 passed; all of `tests/llm/providers/langchain` plus the verify
      formatting/orchestration modules clean apart from the known environmental
      failures. `mcp-coder check file-size --max-lines 750` flags only the
      pre-existing `tests/cli/commands/test_verify_orchestration.py` (871 lines,
      grown by steps 3-4), which step 8 does not touch;
      `test_langchain_verification.py` shrank to 537 lines and
      `verification.py` is at 583.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-7: the `.venv` copy of the unpinned git dependency `mcp-workspace` lacks
      `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and pytest
      collects zero tests (confirmed again this run: the first unshimmed run
      collected 0). Same workaround: a throwaway `.pytest_shim/sitecustomize.py`
      registering a stand-in `mcp_workspace.checks.branch_status_rendering`
      (re-export `CIStatus` from `mcp_workspace.checks.branch_status`, any str
      for `GITHUB_TOKEN_HINT`), run pytest with
      `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the directory afterwards
      — it is **not** committed. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the six
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API), excluded via
      `--ignore-glob` for the 996-test `tests/cli` run; the three
      `tests/llm/providers/copilot/test_copilot_integration.py` tests (no
      working `copilot` CLI); and
      `test_langchain_exceptions.py::…httpx_connect_error` (`httpx` absent →
      MagicMock).)
- [x] Commit message prepared

### Step 9: Contract findings in `verify` + exit-code wiring

Details: [step_9.md](./steps/step_9.md)

- [x] Implementation (tests + production code)
      (`verify_langchain` calls step 5's `validate()` once and merges the
      findings into the result. Two new helpers in `verification.py`:
      `_row_from()` — when a finding exists **both** its `ok` and its `value`
      win, so the `API key` row carries the contract message naming `api_key`
      and `OPENAI_API_KEY` rather than a bare `not set`; and
      `_api_key_default_value()` for the no-finding branch, which never returns
      a bare `_mask_api_key(key)` (that yields None → `_format_section`
      stringifies it to the literal `"None"`). The hand-rolled
      `backend == "ollama"` api_key special case is **deleted** — the contract
      already declares api_key optional there — while its
      `"not set (optional)"` text is preserved. `_resolve_api_key` is now
      passed `mode`, not `backend`, and a source with no readable key (gemini's
      keyless Vertex carve-out) renders `satisfied via {source}`, never
      `[OK] not set (optional)` on a `required` row. The `backend` row is
      **overwritten** when a `backend` finding exists, so an unsupported
      backend is explained instead of rendering `[OK] opnai` next to exit 1;
      `base_url` / `api_version` findings arrive via `setdefault`. Defaults are
      **contract-aware**: `validate()` short-circuits when `mode_of()` is None,
      so `scoped=False` falls back to today's presence test and the plain
      `"not set"` text — a typo'd or unset backend never renders
      `Model [OK] None`. `overall_ok` gains
      `all(f["ok"] is not False for f in findings.values())`, so errors exit 1
      while `ok=None` warnings stay exit-neutral; `verify_exit_code.py` is
      untouched, as specified. `_LABEL_MAP` gains `"base_url": "Base URL"` and
      `"api_version": "API version"`.

      **Test placement note.** TDD cases 1-6, 8 and 8b live in the new
      `tests/llm/providers/langchain/test_langchain_contract_rows.py`
      (20 tests) rather than in `test_langchain_verification.py` as
      step_9.md's WHERE suggests: that file is at 542 lines and the new
      coverage is ~300, the same reasoning steps 7 and 8 used when they split.
      Every case that says "assert the rendered row too" renders through the
      real `_format_section` + `_LABEL_MAP`. TDD case 7 is in
      `tests/cli/commands/test_verify_exit_codes.py` as
      `TestContractViolationExitCode` — the one class there that leaves
      `verify_langchain` **un-mocked**, so a finding produced inside the
      provider really does reach `_compute_exit_code`; it patches
      `_load_langchain_config` on the *verification* module, which holds its
      own binding from a module-level `from . import`. A companion test pins
      that a sound config still exits 0.

      **Two existing tests changed, both because step 9 deliberately changes
      their subject.** `test_no_api_key_overall_ok_true` asserted exit-neutral
      behaviour for an openai config with no credential anywhere — precisely
      what TDD case 2 makes exit 1 — so it is renamed
      `test_no_api_key_fails_the_contract` and now also asserts the message
      names `OPENAI_API_KEY`; its original point (no test prompt is sent) is
      kept. `test_row_added_when_env_var_supplied_the_url` in
      `test_langchain_effective_config.py` asserts `overall_ok is True` to show
      the redirect row is exit-neutral, but used a keyless config; it now
      supplies an `api_key` so the assertion still tests the redirect row
      rather than the contract.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in any file this step touches**: pylint scoped to the
      six touched source/test files reports only the environmental `E0401`
      (`langchain_mcp_adapters` not installed); mypy over
      `src/mcp_coder/llm/providers/langchain`, `src/mcp_coder/cli/commands`,
      `tests/llm/providers/langchain` and `tests/cli/commands` reports only the
      4 known `check_branch_status` findings; ruff clean; isort clean; black
      reformatted the two new/extended test files once and is now a no-op
      across 623 files. lint-imports: 21 contracts kept. Step 9's own tests
      pass — `test_langchain_contract_rows.py` + `test_verify_exit_codes.py`
      → 38 passed. Wider runs: `tests/cli` → 1002 passed; all of
      `tests/llm/providers/langchain` clean apart from the known environmental
      failure. `mcp-coder check file-size --max-lines 750` flags only the
      pre-existing `tests/cli/commands/test_verify_orchestration.py`
      (871 lines, grown by steps 3-4), which step 9 does not touch;
      `verification.py` is at 641 lines.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-8: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and
      pytest collects zero tests (confirmed again this run: the first
      unshimmed run collected 0). Same workaround: a throwaway
      `.pytest_shim/sitecustomize.py` registering a stand-in
      `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus` from
      `mcp_workspace.checks.branch_status`, any str for `GITHUB_TOKEN_HINT`),
      run pytest with `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the
      directory afterwards — it is **not** committed (`git status` confirms
      only the six intended files). Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the six
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API), excluded via
      `--ignore-glob` for the 1002-test `tests/cli` run; the three
      `tests/llm/providers/copilot/test_copilot_integration.py` tests (no
      working `copilot` CLI); and
      `test_langchain_exceptions.py::…httpx_connect_error` (`httpx` absent →
      MagicMock). **One addition to the baseline, newly observed because this
      run widened to all of `tests/llm`:** the 10 tests in
      `tests/llm/providers/claude/test_llm_sessions.py` fail with
      `MockClaudeCLI.__call__() got an unexpected keyword argument
      'settings_file'` — a claude-CLI signature drift in that module's own
      mock. Verified independent of this step: the file is untracked-clean in
      `git status`, imports nothing from `verification.py` or
      `verify_formatting.py`, and `settings_file` appears nowhere in the
      langchain provider.)
- [x] Commit message prepared

### Step 10: Connection errors name the host actually dialed

Details: [step_10.md](./steps/step_10.md)

- [x] Implementation (tests + production code)
      (`_handle_provider_error` gains `dialed: str | None = None` and folds it
      into one local — `hint = f"tried {dialed}" if dialed else base_url_hint`
      — used by **both** `raise_connection_error` sites, so the gemini
      non-auth-`ClientError` branch names the host too, not just the
      `CONNECTION_ERRORS` branch. `_exceptions.raise_connection_error` is
      untouched; it already renders the value as `  2. base_url: {hint}`. The
      falsy guard is deliberate: `dialed=""` falls back to the static hint
      rather than printing a bare `tried `. Threaded at **all four** call
      sites with step 6's `dialed_url(chat_model)` — `_ask_text:365`,
      `_ask_agent:441`, `_ask_agent_stream:599` (the held-thread exception)
      and `_ask_text_stream:724` — no plumbing needed, `chat_model` is already
      the local each `except` block sits under. `dialed_url` joins `validate`
      on the existing module-level `from ._config_diagnostics import`, which
      stays cycle-free because that module imports stdlib only.
      Consequence worth stating: a backend whose `_BACKEND_ERROR_PARAMS` hint
      is `""` (gemini, anthropic) now gets a `base_url:` line it never had.

      `verification.py`: the `_list_models_for_backend` connection branch
      appends `— tried {base_url}` when a base_url was handed to the SDK. This
      is the one place the value is *not* read off a constructed client —
      there is no langchain client on that path, only the raw SDK call — so it
      is omitted entirely rather than guessed when `base_url` is None, which
      also leaves the existing `test_connection_error_message_preserved`
      (base_url=None) exact-match assertion valid.

      **Test placement note.** The 17 tests live in the new
      `tests/llm/providers/langchain/test_langchain_dialed_host.py` rather than
      being split across `test_langchain_provider.py` (664 lines) and
      `test_langchain_verification.py` (543) as step_10.md's WHERE suggests:
      the provider file would have passed the 750-line limit, and the four
      provider-path tests plus the `--check-models` tests are one subject. Same
      reasoning steps 7-9 used. TDD cases 1-4 are all covered, plus: the empty
      -string guard, the ollama and anthropic hint variants, auth errors *not*
      naming the host, the gemini second branch, and a `dialed_url() -> None`
      client keeping today's message. Every provider-path test leaves
      `config["base_url"]` unset while the stub client reports
      `https://relay.internal/v1`, so the assertion can only pass if the value
      came off the client — which is the whole point of the step.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in any file this step touches**: pylint scoped to
      `__init__.py`, `verification.py` and the new test file reports nothing
      beyond the environmental `E0401`; mypy over
      `src/mcp_coder/llm/providers/langchain` + `tests/llm/providers/langchain`
      is clean; ruff clean; isort clean; black reformatted the new test file
      and `__init__.py` once and is now a no-op across 624 files.
      lint-imports: 21 contracts kept. Step 10's own tests pass —
      `test_langchain_dialed_host.py` → 17 passed. Wider runs:
      `tests/llm/providers/langchain` → 579 passed, 1 deselected (the known
      httpx failure); `tests/cli` → 998 passed.
      `mcp-coder check file-size --max-lines 750` flags only the pre-existing
      `tests/cli/commands/test_verify_orchestration.py` (871 lines, grown by
      steps 3-4), which step 10 does not touch; `__init__.py` is at 731 lines
      and the new test file at 288.

      **One finding was real and is fixed:** pylint `W0101` (unreachable) on
      the first spelling of the agent-stream stub, a
      `raise`-then-`yield` async generator. Replaced with a small
      `_RaisingAsyncIter` class — the shape
      `test_langchain_agent_streaming.py` already uses for the same purpose.

      **Order-of-work note:** unlike steps 1-9 this step's production edit
      landed before the tests were written, so the tests were green on first
      run rather than red-then-green. They are not vacuous — every case-1/3
      assertion matches on the literal `tried `, a string that exists nowhere
      in the pre-change tree — but the TDD convention in `summary.md` was not
      followed to the letter here.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-9: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and
      pytest collects zero tests (confirmed again this run: the first
      unshimmed run collected 0). Same workaround: a throwaway
      `.pytest_shim/sitecustomize.py` registering a stand-in
      `mcp_workspace.checks.branch_status_rendering` (re-export `CIStatus` from
      `mcp_workspace.checks.branch_status`, any str for `GITHUB_TOKEN_HINT`),
      run pytest with `env_vars={"PYTHONPATH": ".pytest_shim"}`, delete the
      directory afterwards — it is **not** committed (`git status` confirms
      only the three intended files). Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Known-failing baseline under the shim** — all environmental, all
      pre-existing, none in files this step touches: the six
      `tests/cli/commands/test_check_branch_status*.py` modules (stale
      `CIStatus.UNAVAILABLE` / `BranchStatusReport` API), excluded via
      `--ignore-glob` for the 998-test `tests/cli` run; and
      `test_langchain_exceptions.py::TestErrorTuples::…httpx_connect_error`
      (`httpx` absent → `CONNECTION_ERRORS` falls back to `(ConnectionError,)`
      at import time, before the conftest MagicMock lands). That fallback is
      also why the new tests raise a plain `ConnectionError` rather than an
      `httpx.ConnectError`.)
- [x] Commit message prepared

### Step 11: `--check-models` cross-checks the configured model

Details: [step_11.md](./steps/step_11.md)

- [x] Implementation (tests + production code)
      (`_check_model_listed(model, listing)` lands in `verification.py` next to
      `_check_base_url_shape`, and is wired in the one place the listing already
      exists — inside `if check_models and backend:`, immediately after
      `result["available_models"]` is populated — so it rides on that network
      call rather than making a second one, and the key is structurally absent
      without `--check-models`. Near-misses call
      `utils.config_hints.suggest()` from step 2 (imported absolutely as
      `from mcp_coder.utils.config_hints import suggest`, matching the
      package's existing `from mcp_coder.utils.user_config import …` style;
      lint-imports still 21/21).

      **Advisory by construction, not by convention.** `ok` is only ever `True`
      or `None`, and the call sits *below* the `overall_ok` computation's
      inputs — `model_check` is never read there — so no exit-code wiring was
      needed and `verify_exit_code.py` is untouched. `test_never_reports_false`
      pins this across the cross product of four listing shapes and three model
      values rather than trusting the three happy-path assertions.

      Two ordering details are deliberate and match step_11.md's ALGORITHM: the
      `listing["ok"]` gate runs *before* the empty-model gate (a failed listing
      reports "could not verify" even with no model configured — the listing is
      the thing that could not be checked), and `listing.get("value") or []`
      treats a missing/None `value` as an empty listing, which is exactly what
      `_list_models_for_backend` returns on every error path.

      `_LABEL_MAP` gains `"model_check": "Model available"` next to
      `available_models`, so the row renders under it.

      **Test placement.** The 13 tests go in the existing
      `tests/llm/providers/langchain/test_langchain_verification.py` as
      step_11.md's WHERE specifies — unlike steps 7-10 that file had room
      (543 → 700 lines, under the 750 limit). TDD cases 1-6 are all covered,
      plus: an explicit 404 listing alongside the auth one, `model=None`, a
      missing `value` key, the never-False cross product, and the label-map
      entry.)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (**Zero findings in any file this step touches.** pylint scoped to
      `verification.py`, `verify_formatting.py` and
      `test_langchain_verification.py` reports nothing beyond the environmental
      `E0401` (`langchain_mcp_adapters.client` not installed); mypy over
      `src/mcp_coder/llm/providers/langchain` + `verify_formatting.py` +
      `config_hints.py` + `tests/llm/providers/langchain` is clean; ruff clean;
      isort clean; black reformatted the test file once and is now a no-op
      across 624 files. lint-imports: 21 contracts kept.
      `mcp-coder check file-size --max-lines 750` flags only the pre-existing
      `tests/cli/commands/test_verify_orchestration.py` (871) and the tracker
      itself; `verification.py` is at 700 and the test file at 700.

      Test runs: `test_langchain_verification.py` → **50 passed**;
      `tests/llm/providers/langchain` → **592 passed, 1 skipped** (with the
      known `test_connection_errors_contains_httpx_connect_error` deselected);
      the five `tests/cli/commands/test_verify*.py` modules → **117 passed**.

      **Two environmental failures, both reproduced without this change:**
      `test_langchain_exceptions.py::TestErrorTuples::…httpx_connect_error`
      (`httpx` absent → `CONNECTION_ERRORS` falls back to `(ConnectionError,)`
      at import time, before the conftest MagicMock lands) — the same known
      baseline steps 2-10 recorded. And, **under `-n auto` only**,
      `test_verify.py::TestVerifyGithubTokenSource::test_token_source_config_renders_second_line`
      dies with `PermissionError: [WinError 32]` unlinking
      `.mcp_coder_verify.md`: `_run_mcp_edit_smoke_test` writes that file at a
      *fixed repo-root path*, so two xdist workers running `execute_verify`
      collide on it. Serially the same five files are 117/117 green. Pre-existing
      xdist race in the smoke test's fixed filename, untouched by this step.

      **Environment note — pytest still needs the shim.** Unchanged from steps
      2-10: the `.venv` copy of the unpinned git dependency `mcp-workspace`
      lacks `mcp_workspace/checks/branch_status_rendering.py`, which
      `src/mcp_coder/checks/branch_status.py:17` imports via
      `mcp_coder/__init__.py:37`, so a bare `import mcp_coder` raises and pytest
      collects zero tests (confirmed again: the first unshimmed run collected
      0). Same workaround — a throwaway `.pytest_shim/sitecustomize.py`
      registering a stand-in `mcp_workspace.checks.branch_status_rendering`,
      `env_vars={"PYTHONPATH": ".pytest_shim"}`, directory deleted afterwards
      and **not** committed. It is also why the unscoped mypy run showed three
      stale-API errors in `cli/commands/check_branch_status.py`
      (`pr_feedback_undeterminable`, `fail_on_reviews`) — same dependency, not
      this step. Real fix needs a shell:
      `pip install --force-reinstall --no-deps "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"`
      then `pip install -e ".[langchain]"`.

      **Order-of-work note:** as in step 10, the production edit landed with the
      tests rather than after a red run, so they were green on first execution.
      They are not vacuous — every assertion matches on strings
      (`not offered by the server`, `does not expose /models`,
      `Model available`) that exist nowhere in the pre-change tree, and the
      import of `_check_model_listed` would have been a collection error.)
- [x] Commit message prepared

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
