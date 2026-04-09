# Issue #720: ICoder — Make Skills Available as Slash Commands

## Goal

Make Claude Code skills (`.claude/skills/*/SKILL.md`) available as slash commands in iCoder. Skills are discovered from the project directory, parsed into typed models, and registered in the existing `CommandRegistry`. Provider-aware: Claude Code gets raw input (handles skills natively), langchain gets the expanded prompt template.

## Architectural / Design Changes

### New Dataclass Fields (existing types)

- **`Response.llm_text: str | None`** — When set and `send_to_llm=True`, the UI layer passes `llm_text` to `stream_llm()` instead of the original user input. This enables langchain provider branching without changing the streaming pipeline.
- **`Command.show_in_help: bool`** — Skills register with `show_in_help=False`. The `/help` handler filters on this field. Autocomplete is unaffected — skills still appear in the dropdown.

### New Method on `CommandRegistry`

- **`add_command(command: Command)`** — Direct imperative registration (vs. the existing decorator). Skills are discovered at startup and registered programmatically, so the decorator pattern doesn't fit. Built-in commands continue using the decorator.

### New Module: `src/mcp_coder/icoder/skills.py`

Single file containing:
- **`ClaudeSkill`** — Full Claude Code skill spec. Parses all frontmatter attributes from SKILL.md (name, description, argument-hint, disable-model-invocation, user-invocable, allowed-tools, model, effort, context, agent, hooks, paths, shell) plus the markdown body (prompt template).
- **`ICoderSkillCommand`** — Thin wrapper for iCoder runtime. Holds reference to `ClaudeSkill` + `command_name`. Extension point for future iCoder-specific fields.
- **`load_skills(project_dir)`** — Discovers `.claude/skills/*/SKILL.md`, parses via `python-frontmatter`, filters out `user-invocable: false`, skips malformed files with warning.
- **`register_skill_commands(registry, skills, provider)`** — Creates provider-aware handlers, skips name collisions with built-ins (warning log), registers with `show_in_help=False`.

### Startup Wiring Change

`execute_icoder()` currently lets `AppCore` create its own default registry. After this change, the CLI layer explicitly creates the registry, loads skills, registers them, and passes the registry to `AppCore`:

```
registry = create_default_registry()
skills = load_skills(project_dir)
register_skill_commands(registry, skills, provider)
app_core = AppCore(llm_service, event_log, registry=registry, ...)
```

### Provider Branching

- **Claude Code** (`provider="claude"`): handler returns `Response(send_to_llm=True)` — raw user input flows through. Claude Code handles skills natively.
- **Langchain** (`provider="langchain"`): handler returns `Response(send_to_llm=True, llm_text=expanded_prompt)` — SKILL.md body with `$ARGUMENTS` replaced by user args.

### New Dependency

`python-frontmatter` — parses YAML frontmatter + markdown body. Added to `dependencies` in `pyproject.toml`.

## Files Created

| File | Purpose |
|------|---------|
| `src/mcp_coder/icoder/skills.py` | ClaudeSkill, ICoderSkillCommand, load_skills, register_skill_commands |
| `tests/icoder/test_skills.py` | All skill-related tests |

## Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | Add `python-frontmatter` dependency |
| `src/mcp_coder/icoder/core/types.py` | Add `llm_text` to Response, `show_in_help` to Command |
| `src/mcp_coder/icoder/core/command_registry.py` | Add `add_command()` method |
| `src/mcp_coder/icoder/core/commands/help.py` | Filter on `show_in_help` in `/help` output |
| `src/mcp_coder/icoder/ui/app.py` | Route `response.llm_text` to `_stream_llm()` |
| `src/mcp_coder/cli/commands/icoder.py` | Create registry, load skills, register, pass to AppCore |
| `tests/icoder/test_types.py` | Test new fields on Response and Command |
| `tests/icoder/test_command_registry.py` | Test add_command and show_in_help filtering |
| `tests/icoder/test_app_core.py` | Test llm_text passthrough from handle_input |
| `tests/icoder/test_cli_icoder.py` | Test skill loading in execute_icoder startup |

## Implementation Steps

1. **Foundation**: Add fields to `Response` and `Command`, add `add_command()` to registry, update `/help` filter
2. **Skill models and loader**: `ClaudeSkill`, `ICoderSkillCommand`, `load_skills()` in `skills.py`, add `python-frontmatter` dependency
3. **Registration and provider branching**: `register_skill_commands()`, `app.py` llm_text routing
4. **Startup wiring**: Connect everything in `execute_icoder()`
