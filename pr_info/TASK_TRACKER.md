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

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: Per-backend contract validator (Azure rule included)

Details: [step_5.md](./steps/step_5.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: `resolve_target()`: read the dialed URL off the constructed client

Details: [step_6.md](./steps/step_6.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

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
