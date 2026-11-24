# Step 2: Scope each session's Bash grants to its binding entries

Read `pr_info/steps/summary.md` first (section "Design", part 1).

## LLM prompt

> Implement step 2 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_2.md`. Write or adapt the tests first, then change the
> four session call sites. Do not change `llm_permissions` itself. Run pylint,
> pytest (unit markers excluded as in CLAUDE.md) and mypy. All must pass. Then format and commit
> as one commit.

## WHERE

- `src/mcp_coder/workflows/implement/task_processing.py`
- `src/mcp_coder/workflows/implement/finalisation.py`
- `src/mcp_coder/workflow_steps/ci.py`
- `src/mcp_coder/workflows/implement/check_loop.py`
- Tests:
  - `tests/workflows/implement/test_task_processing_bash_grants.py`
  - `tests/workflows/implement/test_finalisation.py`
  - `tests/workflow_steps/test_ci_bash_grants.py`
  - `tests/workflows/implement/test_check_loop_fix_turns.py`
  - `tests/workflows/implement/test_check_loop.py`
  - `tests/utils/test_toolkit_permissions.py`

## WHAT

`llm_permissions(project_dir, provider, entry)` in `utils/toolkit_runner.py` is used unchanged.

- **`task_processing.py`** (around line 186):
  ```python
  # The task session's work is checked against both implement bindings
  permissions = llm_permissions(project_dir, provider, "implement_task") + llm_permissions(
      project_dir, provider, "implement_final"
  )
  bash_grants = bash_grants_of(list(dict.fromkeys(permissions)))
  ```
- **`finalisation.py`** (line 71): `bash_grants_of(llm_permissions(project_dir, provider, "implement_final"))`
- **`ci.py`** (around line 207): `bash_grants_of(llm_permissions(config.project_dir, config.provider, "implement_final"))`
- **`check_loop.py`**:
  - `_fix_turn(...)` gets a new last parameter `entry: str`, documented as "Binding entry being fixed; scopes the session's Bash grants".
  - Inside it: `bash_grants = bash_grants_of(llm_permissions(project_dir, provider, entry))`.
  - `toolkit_declares_bash_grants(project_dir)` and the `resolve_prompt_slots("[check_instructions]", …, bash_grants)` call stay as they are.
  - `check_and_fix` passes its `entry` to `_fix_turn`.

## HOW

- No new imports or helpers.
- Each call site's comment says why it uses that scope (least privilege: the session gets grants only for the depths its work is checked against).
- `resolve_prompt_slots` (step 1) turns the scoped grants into the matching re-run list, in the task template and also in the injected system prompt via `prompt_llm(bash_grants=...)`.

## ALGORITHM

```
task session:  perms = llm_permissions(.., "implement_task") + llm_permissions(.., "implement_final")
               grants = bash_grants_of(list(dict.fromkeys(perms)))
finalisation:  grants = bash_grants_of(llm_permissions(.., "implement_final"))
ci fix:        grants = bash_grants_of(llm_permissions(.., "implement_final"))
fix turn:      grants = bash_grants_of(llm_permissions(.., entry))   # entry from check_and_fix
```

## DATA

`bash_grants: list[str]`, deduplicated, in binding order: `implement_task` grants first, then `implement_final`.

## Tests (write first)

- **`test_task_processing_bash_grants.py`:**
  - `llm_permissions` is called with `(project, "claude", "implement_task")` and `(project, "claude", "implement_final")`.
  - Overlapping grants from the two calls (use `side_effect` returning two lists sharing one grant) reach `prompt_llm` once each, in order.
- **`test_finalisation.py`** and **`test_ci_bash_grants.py`:** `llm_permissions` is called with entry `"implement_final"`.
- **`test_check_loop_fix_turns.py`:**
  - `_turn()` passes an entry.
  - `mocks.perms.assert_called_once_with(_PROJECT, "claude", "implement_task")`.
  - The `toolkit_declares_bash_grants` call is unchanged.
- **`test_check_loop.py`:** `check_and_fix(..., entry="implement_task")` forwards `"implement_task"` to `_fix_turn`. Extend `test_forwards_llm_params_to_fix_turn`.
- **Acceptance**, in `tests/utils/test_toolkit_permissions.py`. Use a real command-toolkit project in `tmp_path`: root `mcp-coder.toml`, default bindings, steps for `check.quick`, `check.standard`, `check.full`, `test.quick`, `test.unattended`, `test.mutation`, `format.apply` and `format.check`, each with a distinct argv. `tests/workflows/rebase/test_prompt.py::_command_project` shows how to build one. Assert:
  - `implement_task` → only the `check.quick` grant;
  - `implement_final` → only the `check.standard` and `test.quick` grants;
  - neither entry yields grants for `check.full`, `test.mutation`, `format.apply` or `format.check`.
- **Acceptance, re-run list**, also in `tests/utils/test_toolkit_permissions.py`, on the same real project. Build the scoped grants the way the sessions do:
  - task session: `bash_grants_of(list(dict.fromkeys(llm_permissions(p, "claude", "implement_task") + llm_permissions(p, "claude", "implement_final"))))`;
  - finalisation / CI fix: `bash_grants_of(llm_permissions(p, "claude", "implement_final"))`.

  Pass each into `resolve_prompt_slots("[check_instructions]", p, "claude", grants)` and assert:
  - task session: the listed commands (the `` - `…` `` lines after `RERUN_INTRO`) are exactly the steps of `check.quick`, `check.standard` and `test.quick`;
  - both cases: none of the `check.full`, `test.mutation`, `format.apply` or `format.check` commands appears in the text.
