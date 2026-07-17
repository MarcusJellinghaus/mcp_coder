# Step 4 — `user-invocable: false` absent from registry + flag doc-note

**Reference:** `pr_info/steps/summary.md`
**Acceptance criteria:** AC5, AC6 (flag doc-note)
**Commit:** one — test + field doc-note + checks passing.

## Goal

- **AC5:** assert the *observable* registry outcome — a `user-invocable: false`
  skill is dropped in `load_skills` and therefore never registered as a command
  (absent from the registry). An existing test only checks the loader list;
  this adds the registry-level assertion.
- **AC6 (flag):** document at the `disable_model_invocation` field definition
  that the flag is **structurally satisfied** (all slash commands are
  user-initiated) and must **not** gain a runtime reader that skips command
  registration — that would wrongly hide human-invocable skills. No silent dead
  flag.

## TDD order

1. Add the registry-outcome test to `test_skills.py`.
2. Add the field doc-note in `skills.py`.
3. Run all three quality gates.

## WHERE

- **Modify:** `tests/icoder/test_skills.py` (uses the existing `_create_skill`
  helper; `load_skills`, `register_skill_commands`, `CommandRegistry` already
  imported)
- **Modify:** `src/mcp_coder/icoder/skills.py` (field doc-note only)

## WHAT

### Test (`test_skills.py`)

```python
def test_user_invocable_false_skill_absent_from_registry(tmp_path: Path) -> None:
    """A user-invocable: false skill is never registered as a command.

    load_skills drops it, so register_skill_commands never sees it and the
    registry has no matching command (observable outcome, not just loader list).
    """
    _create_skill(
        tmp_path,
        "hidden",
        'description: "Hidden"\nuser-invocable: false\n',
        "body",
    )
    registry = CommandRegistry()
    skills = load_skills(tmp_path)
    register_skill_commands(registry, skills, "langchain")
    assert registry.has_command("/hidden") is False
```

### Production edit (field doc-note only)

In `skills.py`, at the `disable_model_invocation` field of the `ClaudeSkill`
dataclass, add an inline comment explaining structural satisfaction. Replace:

```python
    disable_model_invocation: bool = False
```

with:

```python
    # Parsed for Claude-format fidelity but intentionally UNREAD at runtime
    # (#1040). In the langchain/TUI path every slash command is user-initiated
    # (model output never reaches handle_input/dispatch — see AppCore module
    # docstring), so the flag's invariant "the LLM may not invoke this skill"
    # holds structurally for all commands. Do NOT add a runtime reader that
    # skips command registration: that would wrongly hide human-invocable
    # skills. Coupled to I1.1/M2, where skill frames can override `never`.
    disable_model_invocation: bool = False
```

## HOW

- The test exercises the real path `load_skills` -> `register_skill_commands`
  -> `registry.has_command`, asserting the negative outcome.
- The doc-note is a comment on the dataclass field; behaviour is unchanged
  (the field is still parsed and assigned in `load_skills`).

## ALGORITHM (test core)

```
create a SKILL.md with `user-invocable: false`
skills = load_skills(tmp_path)          # drops the hidden skill
register_skill_commands(registry, skills, "langchain")
assert registry.has_command("/hidden") is False
```

## DATA

- Test asserts `registry.has_command("/hidden") is False`.

## Quality gates

Run pylint, pytest (fast exclusion set, `-n auto`), mypy. `format_all.sh`
before commit.

## LLM prompt

> Implement Step 4 from `pr_info/steps/step_4.md` (context in
> `pr_info/steps/summary.md`). Using the MCP workspace tools only:
> (1) add `test_user_invocable_false_skill_absent_from_registry` to
> `tests/icoder/test_skills.py` using the existing `_create_skill` helper;
> (2) add the specified doc-note comment above the `disable_model_invocation`
> field in `src/mcp_coder/icoder/skills.py`, changing no behaviour. Then run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check`
> (`extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`),
> and `mcp__tools-py__run_mypy_check`; fix until all pass. This is one commit.
