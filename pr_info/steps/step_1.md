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

## WHAT

`prompt_slots.py`:

```python
RERUN_INTRO = (
    "Re-run the checks with these exact commands; run each one unchanged — "
    "extra arguments, flags or changed spacing are denied:\n"
)  # moved verbatim from toolkits/command/toolkit.py (_RERUN_INTRO)

def resolve_prompt_slots(text, project_dir, provider, bash_grants) -> dict[str, str]
    # signature unchanged; only the check_instructions rule changes
```

`toolkits/command/toolkit.py`:

- delete `_RERUN_INTRO`;
- add `from mcp_coder.utils.prompt_slots import RERUN_INTRO`;
- use `RERUN_INTRO` in `prompt_fragments()`.

The fragment output is unchanged, so `tests/toolkits/command/test_toolkit_describe.py` must still pass without edits.

## HOW

- `toolkit_declares_bash_grants(project_dir)` is unchanged. It still decides "is this a Bash toolkit" over everything declared.
- `resolve_prompt_slots` no longer uses the toolkit's `check_instructions` fragment for a Bash toolkit. It builds the list from the `bash_grants` argument.
- Update the module and function docstrings: for a toolkit that declares Bash grants, `check_instructions` lists exactly the session's granted commands.

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
- Keep: no grants (`[]` or `None`) → `""`; a non-Claude provider → `""`; a toolkit without Bash grants → its fragment unchanged.

`tests/llm/test_interface_prompt_slots.py`:

- Update expectations that assumed `_COMMAND_CHECKS` reaches the prompt when `bash_grants` is passed. The sent prompt now contains `RERUN_INTRO` and `` - `make check:*` `` lines built from the grants passed to `prompt_llm`.
- Calls without grants still get no `check_instructions` text.

If `lint-imports` reports a contract violation for the import of `mcp_coder.utils.prompt_slots` from `mcp_coder.toolkits.command.toolkit`, write one line to `pr_info/.blocked.txt` and stop.
