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
      (STILL BLOCKED — confirmed a 4th time. Needs shell access; no run so far has had it.

      NEW THIS RUN — three findings that change the picture:
      1. The venv is behind on FOUR separate upstream features, not just one missing file:
         `branch_status_rendering` (module), `GITHUB_TOKEN_HINT`, `pr_feedback_undeterminable`
         (BranchStatusReport field), `fail_on_reviews` (format_for_llm/format_for_human kwarg)
         and `add_assignees` (PullRequestManager method). So the reinstall must land a revision
         carrying all five names, not merely `a1f0eac`.
      2. An in-repo compat shim is NOT a viable workaround. Verified via `list_symbols` on
         `.venv/.../mcp_workspace/checks/branch_status.py`: the installed copy defines `CIStatus`
         at line 44 and `WaitContext` at line 54, but has NO `GITHUB_TOKEN_HINT` at all. A
         try/except fallback import would therefore require back-porting that constant plus the
         three other upstream features into mcp-coder — clearly wrong.
      3. TRAP FOR THE NEXT RUN: `mcp__tools-py__get_library_source` resolves against the *tooling
         server's* environment, which has a NEWER mcp_workspace than the project `.venv`. Asking
         it for `mcp_workspace.checks.branch_status_rendering` returns the file happily and makes
         the venv look fine. It is not. Use `mcp__workspace__list_directory` on
         `.venv/Lib/site-packages/mcp_workspace/checks` instead — that reads the real project venv
         and shows only 4 files. (`read_file` refuses .venv paths as gitignored; `list_directory`
         and `list_symbols` both work.)

      Root cause (unchanged):
      `mcp-workspace` is an *unpinned* git dependency (`pyproject.toml:348`), and the copy in
      `.venv` predates upstream commit `a1f0eac`, which added `checks/branch_status_rendering.py`.
      Verified directly: `.venv/Lib/site-packages/mcp_workspace/checks/` contains only
      `branch_status.py`, `branch_status_polling.py`, `file_sizes.py`, `pr_feedback.py` — no
      `branch_status_rendering.py`; upstream HEAD has it. `src/mcp_coder/checks/branch_status.py:17`
      imports it, `src/mcp_coder/__init__.py:37` pulls that in, so `import mcp_coder` fails and
      **pytest collects zero tests**. The repo code is correct; the venv is stale.
      - pylint: every finding is a missing-import error (E0401/E0611 from the stale
        `mcp_workspace`, plus optional deps `langchain_core`, `langchain_mcp_adapters`,
        `langgraph`, `httpx`, `mcp` not installed) or an E1123/E1101 downstream of it.
        **No** finding is in a file touched by this step.
      - mypy: 8 errors, all environmental. 7 trace to the stale `mcp_workspace` — `add_assignees`
        (upstream `pr_manager.py:401`), `pr_feedback_undeterminable` (upstream
        `checks/branch_status.py`), `fail_on_reviews` (upstream `checks/branch_status_rendering.py`)
        and `branch_status_rendering` itself, all re-verified present upstream this run; the 8th is
        an untyped decorator caused by the missing optional `mcp` package. **No** error is in a
        file touched by this step.
      Rename re-verified by inspection instead: both TDD deliverables are present
      (`tests/utils/test_user_config_schema.py:217` asserts the `MCP_CODER_LLM_LANGCHAIN_BASE_URL`
      env var, `:221` asserts `endpoint` is gone from the schema;
      `tests/llm/providers/langchain/test_langchain_provider.py:102` asserts the retired env var is
      ignored). The only remaining `endpoint` spellings in `src/` are the intentional ones: the
      `endpoint_shape` result key + `"Endpoint"` label (deferred to step 8), the `azure_endpoint=`
      SDK kwarg, and an unrelated `task_tracker.py` docstring.
      Fix: `pip install --force-reinstall --no-deps
      "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"` in `.venv`
      (optionally also install the langchain/httpx/mcp extras to clear the remaining findings),
      then re-run all three checks.)
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
