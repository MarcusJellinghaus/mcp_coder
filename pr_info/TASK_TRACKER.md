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

## ⚠️ Environment note for EVERY step (read before running pytest)

Not a code defect and **not fixable in-repo** — do not try to "fix" it in `src/`.

The `.venv` copy of the unpinned git dependency `mcp-workspace` (`pyproject.toml:348`) is
stale: `.venv/Lib/site-packages/mcp_workspace/checks/` has no `branch_status_rendering`,
which `src/mcp_coder/checks/branch_status.py:17` imports. Because
`src/mcp_coder/__init__.py:37` pulls that in, a bare `import mcp_coder` raises — so by
default **pytest collects zero tests**. The failing import arrived with commit `bce0f22`
on `origin/main`: pre-existing upstream code, untouched by this branch.

The venv is behind on these upstream names: `branch_status_rendering` (module),
`GITHUB_TOKEN_HINT`, `CIStatus.UNAVAILABLE` / `CIStatus.UNKNOWN` (enum members),
`pr_feedback_undeterminable` (`BranchStatusReport` field), `fail_on_reviews`
(`format_for_llm` / `format_for_human` kwarg), `add_assignees` (`PullRequestManager`
method). Optional extras are absent too: `langchain_core`, `langchain_mcp_adapters`,
`langgraph`, `httpx`, `mcp`, `pytest-textual-snapshot`.

**Real fix** (needs a shell; agent runs have not had one) — in `.venv`:

```
pip install --force-reinstall --no-deps \
  "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"
pip install -e ".[langchain]"
```

**Workaround that lets pytest run WITHOUT a shell** (used to verify step 1; reuse for
steps 2-19): write a throwaway `.pytest_shim/sitecustomize.py` that registers a stand-in
`mcp_workspace.checks.branch_status_rendering` in `sys.modules` — re-export `CIStatus`
from `mcp_workspace.checks.branch_status` and define `GITHUB_TOKEN_HINT` as any str — then
run pytest with `env_vars={"PYTHONPATH": ".pytest_shim"}`. Delete the directory afterwards.
Never commit such a shim into `src/`. Note the full suite exceeds the 300 s tool timeout,
so run it in directory chunks.

**Known-failing baseline under that shim** (all environmental, all pre-existing on main):
branch-status tests in `tests/cli/commands/test_check_branch_status*.py`, `tests/checks/`
and `tests/workflows/review/test_*gates.py` fail on the stale enum/API;
`tests/llm/providers/copilot/test_copilot_integration.py` needs the absent `copilot` CLI;
`test_langchain_exceptions.py::...httpx_connect_error` sees `httpx` as a MagicMock;
`tests/icoder/test_snapshots.py` needs the missing `snap_compare` fixture. Everything else
passes. mypy: 8 errors, all traced to the above. pylint: only E0401/E0611 plus the
E1123/E1101 that follow from them.

**Trap:** `mcp__tools-py__get_library_source` resolves against the *tooling server's*
environment, which has a NEWER mcp_workspace than the project `.venv`, so it happily
returns `branch_status_rendering` and makes the venv look fine. Use
`mcp__workspace__list_directory` on `.venv/Lib/site-packages/mcp_workspace/checks` to see
the truth (`read_file` refuses `.venv` paths as gitignored; `list_directory` and
`list_symbols` both work).

---

## Tasks

### Step 1: Rename `endpoint` → `base_url`

Details: [step_1.md](./steps/step_1.md)

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
      (All three ran; **zero findings in any file this step touches**. Every finding is
      environmental — see the note above. Step 1's own tests execute and pass:
      `tests/utils/test_user_config_schema.py` + `tests/llm/providers/langchain/test_langchain_provider.py`
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
