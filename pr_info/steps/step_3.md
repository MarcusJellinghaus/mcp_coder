# Step 3 — `SendToLLM.allowed_tools` field + skill handler populates it

**Read first:** `pr_info/steps/summary.md` (design change §3).

Add the carrier field and its first producer. Threading through the router / UI /
service happens in later steps.

## WHERE
- Source: `src/mcp_coder/icoder/core/types.py` (`SendToLLM`).
- Source: `src/mcp_coder/icoder/skills.py` (`_make_langchain_handler`).
- Tests: `tests/icoder/test_types.py`, `tests/icoder/test_skills.py`.

## WHAT
```python
@dataclass(frozen=True)
class SendToLLM:
    """Forward `text` to the LLM for streaming."""
    text: str
    allowed_tools: tuple[str, ...] | None = None
```
`_make_langchain_handler`'s inner handler:
```python
return Response(actions=(
    SendToLLM(text=expanded, allowed_tools=tuple(skill.allowed_tools) or None),
))
```

## HOW
- New field is optional with default `None` → backward compatible; every existing
  `SendToLLM(text=…)` construction keeps working.
- `tuple(skill.allowed_tools) or None`: empty list → `None` (no declaration);
  non-empty → a tuple of the declared tokens (verbatim, incl. non-MCP/wildcard —
  classification is the filter's job in Step 1/4).
- `_make_claude_handler` is unchanged (Claude Code path enforces natively).

## ALGORITHM
_(none — data plumbing only)_

## DATA
- `SendToLLM.allowed_tools`: `tuple[str, ...] | None`. `None` = no declaration.

## Tests (write first)
- `test_types`: `SendToLLM(text="x").allowed_tools is None`; a constructed
  `SendToLLM(text="x", allowed_tools=("mcp__srv__a",))` round-trips.
- `test_skills`: a fixture `ClaudeSkill` with `allowed_tools=["mcp__srv__a"]` →
  handler returns `SendToLLM` whose `allowed_tools == ("mcp__srv__a",)`.
- `test_skills`: a fixture skill with `allowed_tools=[]` → handler `SendToLLM.allowed_tools is None`.

## Definition of done
Field + handler updated; both test files pass; checks green. One commit.

## LLM prompt
> Implement Step 3 from `pr_info/steps/step_3.md` (context in `pr_info/steps/summary.md`).
> Using TDD, first add tests to `tests/icoder/test_types.py` and `tests/icoder/test_skills.py`,
> then add the optional `allowed_tools: tuple[str, ...] | None = None` field to `SendToLLM`
> in `core/types.py` and populate it from `skill.allowed_tools` in
> `_make_langchain_handler` (`tuple(...) or None`). Leave `_make_claude_handler` unchanged.
> Run pylint, pytest (unit markers per CLAUDE.md), and mypy; fix all issues. One commit.
