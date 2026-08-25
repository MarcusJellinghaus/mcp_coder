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
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
      (BLOCKED on **pytest only** — environmental, not a code defect. Confirmed again on
      2026-08-25; no run so far has had a shell tool, which is the only thing needed.

      **The one action that unblocks this** — run in `.venv`, then re-run the three checks:
      ```
      pip install --force-reinstall --no-deps \
        "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"
      pip install -e ".[langchain]"   # optional: clears langchain_core/langgraph/httpx/mcp findings
      ```

      **Root cause.** `mcp-workspace` is an *unpinned* git dependency (`pyproject.toml:348`) and
      the `.venv` copy is stale: `.venv/Lib/site-packages/mcp_workspace/checks/` holds only
      `branch_status.py`, `branch_status_polling.py`, `file_sizes.py`, `pr_feedback.py` — no
      `branch_status_rendering.py`. `src/mcp_coder/checks/branch_status.py:17` imports it and
      `src/mcp_coder/__init__.py:37` pulls that in, so `import mcp_coder` raises and **pytest
      collects zero tests** — no test can run, in this step or any other. The failing import
      arrived with commit `bce0f22`, which `git branch --contains` places on `origin/main`:
      pre-existing upstream code, untouched by this branch.

      The venv is behind on five upstream names, so the reinstall must land a revision carrying
      all of them, not merely `a1f0eac`: `branch_status_rendering` (module), `GITHUB_TOKEN_HINT`,
      `pr_feedback_undeterminable` (BranchStatusReport field), `fail_on_reviews`
      (format_for_llm/format_for_human kwarg), `add_assignees` (PullRequestManager method).

      **Verified green (needs no imports, so the stale venv cannot hide anything):**
      - ruff clean; black 615 files unchanged; isort clean.
      - Rename verified complete by inspection at every integration point in step_1.md §HOW:
        `user_config.py:57` (`base_url` + `MCP_CODER_LLM_LANGCHAIN_BASE_URL`), `__init__.py`
        141/149/163/192/218, both backend signatures (`ollama_backend.py:40` local correctly
        renamed to `resolved_url`), `_preflight.py:40`, `_errors_404.py:25,82`,
        `verification.py` (`_check_base_url_shape`, `error_type: "base_url"`), and all hint
        strings. Both TDD deliverables present: `tests/utils/test_user_config_schema.py:220`
        and `tests/llm/providers/langchain/test_langchain_provider.py:101`.
        Only `endpoint` spellings left in `src/`: the `endpoint_shape` key + `"Endpoint"` label
        (step 8), the `azure_endpoint=` SDK kwarg, and an unrelated `task_tracker.py` docstring.
        All intentional.
      - pylint + mypy DID run: **zero findings in any file this step touches.** pylint reports
        only E0401/E0611 missing-imports (stale `mcp_workspace`; plus uninstalled optional deps
        `langchain_core`, `langchain_mcp_adapters`, `langgraph`, `httpx`, `mcp`) and the
        E1123/E1101 that follow from them. mypy reports 8 errors: 7 trace to the stale
        `mcp_workspace`, the 8th is an untyped decorator caused by the missing optional `mcp`.

      **Two traps for the next run:**
      1. `mcp__tools-py__get_library_source` resolves against the *tooling server's* environment,
         which has a NEWER mcp_workspace than the project `.venv`. Ask it for
         `mcp_workspace.checks.branch_status_rendering` and it returns the file happily, making
         the venv look fine. It is not. Use `mcp__workspace__list_directory` on
         `.venv/Lib/site-packages/mcp_workspace/checks` — that reads the real venv. (`read_file`
         refuses .venv paths as gitignored; `list_directory` and `list_symbols` both work.)
      2. An in-repo compat shim is NOT a viable workaround: the installed
         `mcp_workspace/checks/branch_status.py` has no `GITHUB_TOKEN_HINT` (re-confirmed via
         `list_symbols`), so a try/except fallback import would mean back-porting that constant
         plus the four other upstream features into mcp-coder. Don't.)
- [x] Commit message prepared

### Step 2: Unknown-key hints: rename table + "did you mean"

Details: [step_2.md](./steps/step_2.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 3: Warn on the retired `MCP_CODER_LLM_LANGCHAIN_ENDPOINT`

Details: [step_3.md](./steps/step_3.md)

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

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
