# Step 1 — Pure filter function `filter_tools_by_declaration`

**Read first:** `pr_info/steps/summary.md` (design changes §2, fail-closed table).

This step adds the pure, MCPManager-free matching function that is the core of the
enforcement mechanism. It has no dependency on a live MCP connection, so it is
fully unit-testable on its own.

## WHERE
- Source: `src/mcp_coder/llm/providers/langchain/mcp_manager.py` (module-level function,
  no `self`).
- Tests: `tests/llm/test_skill_tool_filter.py` *(new file)*.

## WHAT
```python
from collections.abc import Callable
from typing import Any

def filter_tools_by_declaration(
    tools: list[Any],
    canonical_name_of: Callable[[Any], str | None],
    declared: tuple[str, ...] | list[str],
) -> tuple[list[Any], list[str]]:
    """Narrow `tools` to the exact MCP tokens in `declared`.

    Returns (filtered_tools, warnings). `declared` is assumed truthy/non-empty
    (the caller treats a falsy declaration as "no narrowing"). Fail-closed:
    an empty allow-set yields an empty tool list; un-parseable tokens are
    dropped (never widen the set) and produce a warning.
    """
```

## HOW
- Module-level function near the top of `mcp_manager.py` (after imports). No new
  imports beyond `Callable` / `Any` (already `cast`/`Any` in the file; add `Callable`).
- Not wired into anything yet — Step 4 calls it from `RealLLMService.stream`.

## ALGORITHM
```
allow, warnings = set(), []
for token in declared:
    if token.startswith("mcp__") and "*" not in token and "(" not in token:
        allow.add(token)                       # exact mcp__server__tool
    elif token.startswith("mcp__") or token.startswith("@"):
        warnings.append(f"Skill tool declaration '{token}' is not supported yet "
                        f"and was ignored; the skill runs with a reduced tool set.")
    # else: non-MCP / Bash-style / bare → ignored, no warning
filtered = [t for t in tools if canonical_name_of(t) in allow]
return filtered, warnings
```

## DATA
- Returns `tuple[list[Any], list[str]]`: the kept tools (new list; input never mutated)
  and human-readable warning strings (empty when all tokens are exact or non-MCP).
- `canonical_name_of(tool)` may return `None`; `None` is never in `allow`, so such tools
  are dropped.

## Tests (write first)
Use tiny stub tools, e.g. `SimpleNamespace(canonical="mcp__srv__read_file")` with
`canonical_name_of=lambda t: t.canonical`:
- subset kept, undeclared token dropped.
- empty MCP allow-set (declaration = `("Bash(git add *)",)`) → `[]`, no warning.
- unknown declared tool (`mcp__srv__nope`) → dropped, no warning.
- wildcard (`mcp__srv__*`), group (`@dev`), arg-scoped (`mcp__srv__tool(command=push)`)
  → not matched (restricted to exact-matched) **and** a warning each; never full set.
- two tools with the same bare name but different canonical names → only the declared
  canonical one is kept (disambiguation).
- input list is not mutated (assert the original list is unchanged / identity preserved).
- `canonical_name_of` returning `None` for a tool → that tool dropped.

## Definition of done
`filter_tools_by_declaration` implemented; new test file passes; pylint / pytest / mypy
green. One commit.

## LLM prompt
> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md` for
> context). Using TDD, first create `tests/llm/test_skill_tool_filter.py` covering the
> listed cases, then add the module-level pure function `filter_tools_by_declaration`
> to `src/mcp_coder/llm/providers/langchain/mcp_manager.py` per the signature and
> algorithm. Do not wire it into any caller yet. Run pylint, pytest (`-n auto` with the
> unit-test marker exclusions from CLAUDE.md), and mypy; fix all issues. Produce one commit.
