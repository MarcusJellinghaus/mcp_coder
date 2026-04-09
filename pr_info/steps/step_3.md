# Step 3: Skill Registration, Provider Branching, and UI Routing

**Context**: See `pr_info/steps/summary.md` for full issue context. Steps 1-2 must be complete.

## Goal

Add `register_skill_commands()` that creates provider-aware handlers and registers skills in the `CommandRegistry`. Update `app.py` to route `response.llm_text` to the LLM.

## Prompt

```
Implement Step 3 of issue #720 (see pr_info/steps/summary.md for context).
Steps 1-2 (foundation + models/loader) are complete.

Add registration and UI routing:
1. register_skill_commands(registry, skills, provider) in skills.py
2. Provider branching: Claude Code → raw input, langchain → expanded prompt
3. Update app.py to use response.llm_text when set
4. Write tests first (TDD), then implement.
5. Run all three code quality checks after changes.
```

## Tests First — `tests/icoder/test_skills.py`

### WHERE
`tests/icoder/test_skills.py` — append to existing file from Step 2

### WHAT — new test functions

```python
def test_register_skill_commands_claude_provider() -> None:
    """Claude provider: handler returns Response(send_to_llm=True) with no llm_text."""

def test_register_skill_commands_langchain_provider() -> None:
    """Langchain provider: handler returns Response(send_to_llm=True, llm_text=expanded)."""

def test_register_skill_commands_langchain_substitutes_arguments() -> None:
    """$ARGUMENTS in prompt template is replaced with user args."""

def test_register_skill_commands_langchain_empty_arguments() -> None:
    """Empty args: $ARGUMENTS replaced with empty string, whitespace stripped."""

def test_register_skill_commands_skips_builtin_collision() -> None:
    """Skill matching a built-in command name is skipped with warning."""

def test_register_skill_commands_autocomplete() -> None:
    """Registered skills appear in filter_by_input (autocomplete)."""

def test_register_skill_commands_not_in_help() -> None:
    """Registered skills have show_in_help=False."""

def test_register_skill_commands_multiple_skills() -> None:
    """Multiple skills are all registered."""
```

## Tests — `tests/icoder/test_app_core.py`

### WHERE
`tests/icoder/test_app_core.py` — append one test

### WHAT
```python
def test_handle_input_returns_llm_text(app_core: AppCore) -> None:
    """When a command sets llm_text, it's available on the response."""
```

#### HOW
Register a custom command on the `app_core.registry` using `add_command` that returns `Response(send_to_llm=True, llm_text="override")`, dispatch via `handle_input`, assert `response.llm_text == "override"`.

## Implementation — `src/mcp_coder/icoder/skills.py`

### WHERE
`src/mcp_coder/icoder/skills.py` — append to existing file from Step 2

### WHAT — registration function

```python
def register_skill_commands(
    registry: CommandRegistry,
    skills: list[ClaudeSkill],
    provider: str,
) -> list[ICoderSkillCommand]:
    """Register skills as slash commands in the registry.

    Returns list of ICoderSkillCommand for the successfully registered skills.
    """
```

### ALGORITHM — register_skill_commands pseudocode
```
registered = []
for skill in skills:
    command_name = "/" + skill.name  (e.g. "/issue_analyse")
    if command_name already in registry: log warning, skip
    if provider == "claude":
        handler returns Response(send_to_llm=True)
    else (langchain):
        handler substitutes $ARGUMENTS in skill.prompt_template with joined args
        handler returns Response(send_to_llm=True, llm_text=expanded_prompt)
    registry.add_command(Command(name, description, handler, show_in_help=False))
    registered.append(ICoderSkillCommand(skill, command_name))
return registered
```

### DATA — handler closures

```python
# Claude Code handler (skill captured in closure)
def _make_claude_handler(skill: ClaudeSkill) -> Callable[[list[str]], Response]:
    def handler(args: list[str]) -> Response:
        return Response(send_to_llm=True)
    return handler

# Langchain handler (skill captured in closure)
def _make_langchain_handler(skill: ClaudeSkill) -> Callable[[list[str]], Response]:
    def handler(args: list[str]) -> Response:
        arguments = " ".join(args)
        expanded = skill.prompt_template.replace("$ARGUMENTS", arguments).strip()
        return Response(send_to_llm=True, llm_text=expanded)
    return handler
```

## Implementation — `src/mcp_coder/icoder/ui/app.py`

### WHERE
`src/mcp_coder/icoder/ui/app.py` — `on_input_area_input_submitted` method, line ~90-92

### WHAT
Route `response.llm_text` to `_stream_llm()` when set.

### HOW
```python
# Before (line 90-92):
elif response.send_to_llm:
    output.write("")
    self.run_worker(lambda: self._stream_llm(text), thread=True)

# After:
elif response.send_to_llm:
    output.write("")
    llm_input = response.llm_text or text
    self.run_worker(lambda: self._stream_llm(llm_input), thread=True)
```

**Note**: `llm_input` must be captured as a local variable before the lambda to avoid late-binding issues.

## Commit Message
```
feat(icoder): add skill registration with provider branching and UI routing
```
