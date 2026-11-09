# Step 1 — Slot filler in `mcp_coder.utils.prompt_slots`

See `pr_info/steps/summary.md` ("New module `mcp_coder.utils.prompt_slots`").

## LLM prompt

> Implement Step 1 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_1.md`.
> Write the tests first, then the implementation. Do not change any prompt text or any
> caller other than `get_prompt_with_substitutions` in this step. Run pylint, mypy and
> pytest; all must pass.

## WHERE

- Create `src/mcp_coder/utils/prompt_slots.py`
- Create `tests/utils/test_prompt_slots.py`
- Modify `src/mcp_coder/prompt_manager.py` (`get_prompt_with_substitutions`)
- Modify `tests/test_prompt_manager.py` (add a backslash case)

## WHAT

```python
SLOT_NAMES: tuple[str, ...] = ("language_context", "check_instructions")
DEFAULT_LANGUAGE_CONTEXT = ""
DEFAULT_CHECK_INSTRUCTIONS = (
    "Run the project's quality checks (linters, type checkers, tests) "
    "and fix all issues."
)

def resolve_prompt_slots(
    text: str,
    project_dir: Path,
    provider: str | None,
    bash_grants: Sequence[str] | None,
) -> dict[str, str]: ...

def fill_prompt(
    template: str,
    substitutions: Mapping[str, str],
    slots: Mapping[str, str],
) -> str: ...
```

## HOW

- Imports from `.toolkit_runner`: `load_toolkit`, `llm_permissions`, `bash_grants_of`.
- `resolve_prompt_slots` lazily loads the toolkit only when `text` contains `[slot]` for
  some slot name.
- Provider resolution matches `prompt_llm`:
  `provider or os.environ.get("MCP_CODER_LLM_PROVIDER") or "claude"`.
- `get_prompt_with_substitutions(source, header, substitutions)` becomes
  `return fill_prompt(get_prompt(source, header), substitutions, {})`.

## ALGORITHM

`resolve_prompt_slots`:
```
present = [s for s in SLOT_NAMES if f"[{s}]" in text]; if not present: return {}
values = {language_context: DEFAULT_LANGUAGE_CONTEXT, check_instructions: DEFAULT_CHECK_INSTRUCTIONS}
try: frags = load_toolkit(project_dir).toolkit.prompt_fragments()
     for s in SLOT_NAMES: if s in frags: values[s] = frags[s]
     if bash_grants_of(llm_permissions(project_dir, "claude")) and (resolved provider != "claude" or not bash_grants):
         values["check_instructions"] = ""
except Exception as exc: logger.warning(...); values = defaults
return {s: values[s] for s in present}
```

`fill_prompt`:
```
lines = template.split("\n"); out = []
for line in lines:
    if line.strip() == f"[{s}]" for some s with slots.get(s) == "":
        if out and out[-1].strip() == "" and next line is blank: skip next blank too
        continue (drop line)
    out.append(line)
keys = {**substitutions, **slots}; pattern = r"\[(" + "|".join(map(re.escape, keys)) + r")\]"
return re.sub(pattern, lambda m: keys[m.group(1)], "\n".join(out)) if keys else joined text
```

Blank-line rule: only blank lines adjacent to a removed slot line collapse (two in a row
become one); blank lines elsewhere stay unchanged. A slot sharing a line with other text
is replaced in place (with `""` it simply disappears from that line).

## DATA

- `resolve_prompt_slots` → dict containing only the slots present in `text`
  (e.g. `{"check_instructions": "..."}`); `{}` when none present.
- `fill_prompt` → the filled string.

## Tests (`tests/utils/test_prompt_slots.py`)

Use a fake toolkit object patched over `prompt_slots.load_toolkit` / `prompt_slots.llm_permissions`.

- `resolve_prompt_slots`:
  - no slot in text → `{}` and `load_toolkit` not called;
  - non-empty fragment → inserted;
  - `""` fragment → `""`;
  - missing fragment → neutral default;
  - `load_toolkit` raises `ValueError` → defaults; `prompt_fragments()` raises → defaults;
    `llm_permissions` raises `RuntimeError` → defaults (never raises);
  - toolkit with Bash grants + provider `"copilot"` → `check_instructions == ""`;
  - toolkit with Bash grants + Claude + empty `bash_grants` → `""`;
  - toolkit with Bash grants + Claude + non-empty `bash_grants` → fragment;
  - toolkit without Bash grants + provider `"copilot"` → fragment kept;
  - provider `None` uses `MCP_CODER_LLM_PROVIDER` (monkeypatch env).
- `fill_prompt`:
  - `""` slot on own line removed; surrounding double blank collapsed to one;
    unrelated double blank lines elsewhere preserved;
  - inline slot replaced in place;
  - substitution value containing `\d`, `\1` and `\\` inserted verbatim;
  - substitution value containing `[check_instructions]` not filled again;
  - fragment value containing `[problem_description]` not substituted;
  - `- [ ]`, `[x]` and unknown `[name]` untouched;
  - empty substitutions and slots → template unchanged.
- `tests/test_prompt_manager.py`: existing `"Hello [name]!"` test still passes; add a
  backslash substitution case.
