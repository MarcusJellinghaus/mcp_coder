# Step 3 — System and project prompts, filled on the inject path

See `pr_info/steps/summary.md` ("Where slots are filled"). Requires Step 1.

## LLM prompt

> Implement Step 3 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_3.md`.
> Write the tests first. Fill the prompts in `prompt_llm` and `prompt_llm_stream` after
> `load_prompts` — do not change `load_prompts`. Run pylint, mypy and pytest; all must pass.

## WHERE

- `src/mcp_coder/prompts/system-prompt.md`
- `src/mcp_coder/prompts/project-prompt.md`
- `src/mcp_coder/llm/interface.py` (`prompt_llm`, `prompt_llm_stream`)
- `docs/repository-setup/python.md` ("Prompt Configuration")
- Tests in `tests/llm/` for `interface.py`; prompt-text test in `tests/prompts/`.

## WHAT — prompt text

`system-prompt.md`:

```
## Coding Practices

- Follow the project's existing style and conventions
- Write unit tests for new functionality
- Run the project's quality checks after making changes
- Fix all issues before proceeding

## Quality Standards

- All code must pass the project's quality checks (linters, type checkers, tests)
- No security vulnerabilities should be introduced

[check_instructions]
```

("Add type annotations to new code" is dropped; exactly one `[check_instructions]`, after
the Quality Standards list.)

`project-prompt.md`:

```
# Project Prompt

[language_context]
Follow existing code conventions and patterns.

## Guidelines
...
```

## WHAT — code

Private helper in `llm/interface.py`:

```python
def _fill_injected_prompts(
    system_prompt: str | None,
    project_prompt: str | None,
    project_dir: Path,
    provider: str,
    bash_grants: Sequence[str] | None,
) -> tuple[str | None, str | None]: ...
```

Called in both `prompt_llm` and `prompt_llm_stream` right after `load_prompts`, with the
already-resolved `provider` and the received `bash_grants`.

## HOW

- `from mcp_coder.utils.prompt_slots import fill_prompt, resolve_prompt_slots`
  (`llm` may depend on `utils` per `tach.toml`).
- No change to `load_prompts`, `verify`, or icoder `/info`.

## ALGORITHM

```
text = (system_prompt or "") + "\n" + (project_prompt or "")
slots = resolve_prompt_slots(text, project_dir, provider, bash_grants)   # {} → no toolkit load
if not slots: return system_prompt, project_prompt
fill = lambda p: None if p is None else fill_prompt(p, {}, slots)
return fill(system_prompt), fill(project_prompt)
```

## DATA

Tuple of the (possibly filled) system and project prompts; `None` stays `None`.

## Docs

`docs/repository-setup/python.md`, "Prompt Configuration": add a short paragraph — custom
system/project prompts may use `[language_context]` and `[check_instructions]` on a line of
their own; the configured toolkit fills them (an empty fragment removes the line, a missing
one gives a neutral default); a file without these placeholders is sent unchanged.

## Tests

- `inject_prompts=True`, slot-free custom prompts → `load_toolkit` not called, prompts
  passed unchanged to the provider.
- Shipped prompts + fake `command`-style toolkit (Bash grants, non-empty
  `check_instructions`) + no `bash_grants` → system prompt has no `[check_instructions]`
  line and no command text.
- Same toolkit + Claude + `bash_grants` given → command text present.
- Fake Python-style toolkit (MCP grants only) → its `check_instructions` and
  `language_context` inserted.
- `prompt_llm_stream` covered by one equivalent test.
- Prompt-text test: `system-prompt.md` and `project-prompt.md` contain no `pylint`,
  `mypy`, `pytest`, `mcp__mcp-tools-py__` or (case-insensitive) `python project`; the
  system prompt contains `[check_instructions]` exactly once.
