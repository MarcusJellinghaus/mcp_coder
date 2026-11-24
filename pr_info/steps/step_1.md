# Step 1: Build the `check_instructions` re-run list from the session's Bash grants

Read `pr_info/steps/summary.md` first (section "Design", part 2).

## LLM prompt

> Implement step 1 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_1.md`. Write the tests first, then change
> `src/mcp_coder/utils/prompt_slots.py` and
> `src/mcp_coder/toolkits/command/toolkit.py`. Do not touch the workflow
> callers. That is step 2. Run pylint, pytest (unit markers excluded as in
> CLAUDE.md), mypy and lint-imports. All must pass. Then format and commit as one commit.

## WHERE

- `src/mcp_coder/utils/prompt_slots.py`
- `src/mcp_coder/toolkits/command/toolkit.py`
- `tests/utils/test_prompt_slots.py`
- `tests/llm/test_interface_prompt_slots.py`
- `tests/toolkits/command/test_toolkit_describe.py`

## WHAT

`prompt_slots.py`:

```python
RERUN_INTRO = (
    "Re-run the checks with these exact commands; run each one unchanged — "
    "extra arguments, flags or changed spacing are denied:\n"
)  # same text as the command toolkit's _RERUN_INTRO, which stays for check_instructions.unattended

def resolve_prompt_slots(text, project_dir, provider, bash_grants) -> dict[str, str]
    # signature unchanged; only the check_instructions rule changes
```

`resolve_prompt_slots` is the only place that builds the `check_instructions` re-run list.

`toolkits/command/toolkit.py`:

- `prompt_fragments()` returns `"check_instructions": ""` in every case. It no longer builds `_RERUN_INTRO + _steps_text(all_steps)`. Remove the now-unused `all_steps` local.
  - Keep the key. With `llm_permissions = "none"` or a global config error, `toolkit_declares_bash_grants` is False, so `resolve_prompt_slots` uses this `""` fragment. Without the key it would fall back to `DEFAULT_CHECK_INSTRUCTIONS`.
- Keep `_RERUN_INTRO` and `_steps_text` unchanged; `check_instructions.unattended` still uses them.
- Do **not** import anything from `mcp_coder.utils.prompt_slots`; `RERUN_INTRO` is not moved across layers.
- Update the `prompt_fragments` docstring: `check_instructions` is always `""`, because `resolve_prompt_slots` builds the re-run list from the session's grants. `check_instructions.unattended` lists the unattended test steps.

## HOW

- `toolkit_declares_bash_grants(project_dir)` is unchanged. It still decides "is this a Bash toolkit" over everything declared.
- `resolve_prompt_slots` no longer uses the toolkit's `check_instructions` fragment for a Bash toolkit. It builds the list from the `bash_grants` argument.
- Update the module and function docstrings: for a toolkit that declares Bash grants, `check_instructions` lists exactly the session's granted commands.
- Rebase sessions pass their per-binding grants to `prompt_llm`. Their injected system prompt's `[check_instructions]` therefore lists only the rebase binding's grants (Decision 4). The rebase code doesn't change.

## ALGORITHM (inside the existing `try` of `resolve_prompt_slots`)

```
fragments → values (unchanged)
resolved = provider or env MCP_CODER_LLM_PROVIDER or "claude"
if toolkit_declares_bash_grants(project_dir):
    if resolved != "claude" or not bash_grants: values["check_instructions"] = ""
    else: values["check_instructions"] = RERUN_INTRO + "\n".join(
              f"- `{g[len('Bash('):-1]}`" for g in bash_grants)
```

## DATA

`check_instructions` for a Bash toolkit, Claude, grants `["Bash(npm run lint)", "Bash(npm test)"]`:

```
Re-run the checks with these exact commands; run each one unchanged — extra arguments, flags or changed spacing are denied:
- `npm run lint`
- `npm test`
```

## Tests (write first)

`tests/utils/test_prompt_slots.py`:

- Adapt the tests that expect the fragment text (`"Run make"`) for a Bash toolkit with grants. They must now expect `RERUN_INTRO + "- \`make\`"` when the session passes `["Bash(make)"]`.
- New: the fragment says "everything", but the session passes only `["Bash(npm run lint)"]` → only that command is listed, and the fragment text is not used.
- New: two grants → two lines, in grant order.
- New (rebase scope, no mocks): build a real command-toolkit project in `tmp_path`. Use a root `mcp-coder.toml` with default bindings and steps for `check.quick`, `check.standard`, `test.quick`, `test.standard` and `test.unattended`, each with a distinct argv; `tests/workflows/rebase/test_prompt.py::_command_project` shows how. Compute `grants = bash_grants_of(llm_permissions(project, "claude", "rebase"))` and call `resolve_prompt_slots("[check_instructions]", project, "claude", grants)`. Assert:
  - the listed commands are exactly the steps of `check.standard` and `test.standard`;
  - none of the `check.quick`, `test.quick` or `test.unattended` commands appears.
- Keep: no grants (`[]` or `None`) → `""`; a non-Claude provider → `""`; a toolkit without Bash grants → its fragment unchanged.

`tests/llm/test_interface_prompt_slots.py`:

- Update expectations that assumed `_COMMAND_CHECKS` reaches the prompt when `bash_grants` is passed. The sent prompt now contains `RERUN_INTRO` and `` - `make check:*` `` lines built from the grants passed to `prompt_llm`.
- Calls without grants still get no `check_instructions` text.

`tests/toolkits/command/test_toolkit_describe.py` (`TestPromptFragments`):

- New: a config with granted steps → `fragments["check_instructions"] == ""`.
- `test_grants_verbatim_and_ungranted_marked` and `test_same_name_different_commands_both_listed`:
  - read `check_instructions.unattended` instead, since `_steps_text` formatting lives on there;
  - move their steps under `test.unattended`;
  - keep the same line assertions (intro line, verbatim granted commands, the "can't be re-run" line for the unsafe step, both same-name commands listed).
- `test_keys`, `test_unattended_only_when_declared` and `test_no_grants_empty_instructions` stay as they are.
