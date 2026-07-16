# Step 4 — Service layer: enforcement toggle, `stream(allowed_tools=…)`, filtering + warning

**Read first:** `pr_info/steps/summary.md` (design changes §4, §5; fail-closed table).
**Depends on:** Step 1 (`filter_tools_by_declaration`), Step 2 (`canonical_name`).

Widen the service seam and perform the host-side narrowing. This is where the AC
"agent cannot re-add a tool" is proven at the seam.

## WHERE
- Source: `src/mcp_coder/icoder/services/llm_service.py`
  (`LLMService` Protocol, `RealLLMService`, `FakeLLMService`).
- Tests: `tests/icoder/test_llm_service.py`.

## WHAT
```python
# Protocol
def stream(self, question: str,
           allowed_tools: tuple[str, ...] | None = None) -> Iterator[StreamEvent]: ...

# RealLLMService.__init__  (new arg, keep the rest)
def __init__(self, ..., enforce_skill_tools: bool = False) -> None: ...

# RealLLMService.stream / FakeLLMService.stream
def stream(self, question: str,
           allowed_tools: tuple[str, ...] | None = None) -> Iterator[StreamEvent]: ...

# FakeLLMService.__init__  (signature parity only)
def __init__(self, ..., enforce_skill_tools: bool = False) -> None: ...
```

## HOW
- Import the filter: `from mcp_coder.llm.providers.langchain.mcp_manager import
  filter_tools_by_declaration` (keep the `MCPManager` import under `TYPE_CHECKING`;
  the function is import-safe — no live connection).
- `RealLLMService`: store `self._enforce_skill_tools = enforce_skill_tools`.
- `FakeLLMService`: store the arg (unused/no-op) and record
  `self.last_allowed_tools = allowed_tools` inside `stream` (terminal assertion point).
- Narrowing happens **before** `prompt_llm_stream(tools=…)` — the injection seam is
  untouched, so the M2 gateway insertion point is unaffected.

## ALGORITHM (`RealLLMService.stream`)
```
tools = None
if self._mcp_manager is not None:
    tools = self._mcp_manager.tools()
    if self._enforce_skill_tools and allowed_tools:
        filtered, warnings = filter_tools_by_declaration(
            list(tools), self._mcp_manager.canonical_name, allowed_tools)  # copy — never mutate cache
        tools = filtered
        for w in warnings:
            yield {"type": "permission_warning", "message": w}
for event in prompt_llm_stream(question, ..., tools=tools, ...):
    ... update session_id on "done" ...
    yield event
```

## DATA
- `permission_warning` event: `{"type": "permission_warning", "message": str}` — a plain
  `StreamEvent` (`dict[str, object]`); no enum change needed.
- `FakeLLMService.last_allowed_tools`: `tuple[str, ...] | None` — records the last call.

## Tests (write first)
Use a `FakeMCPManager` exposing `tools()` and `canonical_name(tool)`; monkeypatch
`prompt_llm_stream` to capture `kwargs["tools"]`:
- enforce=True + subset declaration → captured `tools` contains only the declared tool;
  the excluded tool is **absent** (seam proof).
- enforce=True + all-non-MCP declaration → captured `tools == []` (fail-closed).
- enforce=True + no `allowed_tools` → captured `tools` is the **full** list.
- enforce=**False** + declaration present → captured `tools` is the **full** list (no narrowing).
- enforce=True + wildcard token → a `permission_warning` event is yielded before the
  stream, and captured `tools` excludes the un-parseable token (restricted, not full).
- cache not mutated: after `stream`, `manager.tools()` still returns the full list.
- `FakeLLMService(enforce_skill_tools=True)` constructs; `stream(q, allowed_tools=("x",))`
  records `last_allowed_tools == ("x",)` and never filters.
- both services still satisfy the `LLMService` protocol; existing tests remain green.

## Definition of done
Service changes implemented; `tests/icoder/test_llm_service.py` passes; checks green.
One commit.

## LLM prompt
> Implement Step 4 from `pr_info/steps/step_4.md` (context in `pr_info/steps/summary.md`;
> depends on Steps 1–2). Using TDD, first add tests to `tests/icoder/test_llm_service.py`
> for the listed enforcement / warning / cache-safety / parity cases (monkeypatch
> `prompt_llm_stream`, use a fake MCP manager), then widen `stream()` on the `LLMService`
> Protocol, `RealLLMService`, and `FakeLLMService` with `allowed_tools=None`; add
> `enforce_skill_tools: bool = False` to both constructors (no-op on Fake, recording
> `last_allowed_tools`); implement the filtering + `permission_warning` yield in
> `RealLLMService.stream` per the algorithm, filtering a copy of `tools()`. Run pylint,
> pytest (unit markers per CLAUDE.md), and mypy; fix all issues. One commit.
