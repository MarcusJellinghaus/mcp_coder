# Step 1 — Shared message helpers (`_messages.py`)

**Goal:** Create the neutral module with the two helpers. No callers yet — later steps
adopt them one path at a time.

## WHERE

* Create `src/mcp_coder/llm/providers/langchain/_messages.py`
* Create `tests/llm/providers/langchain/test_langchain_messages.py`

## WHAT

```python
def assemble_messages(
    system_messages: list[Any] | None,
    history: list[dict[str, Any]],
    question: str,
) -> list[Any]: ...

def serialize_messages(messages: list[Any]) -> list[dict[str, Any]]: ...
```

## HOW

* `from __future__ import annotations`; module docstring must state **why** the module is
  neutral: `__init__.py` lazy-imports `.agent` to avoid a cycle, so these helpers may not
  live in `__init__.py`. The module must import **nothing** from its own package.
* All `langchain_core` imports are **deferred inside the functions** (matching the
  existing style in `__init__.py` / `agent.py`) so importing the package still works
  without langchain installed.
* Both helpers get full Google-style docstrings with an `Args:` and `Returns:` section.
  **Ruff** enforces this for `src/` — `[tool.ruff.lint]` selects `["D", "DOC"]` with
  `convention = "google"`, and `tests/**/*.py` is exempted via per-file-ignores. Pylint
  does **not**: its whole `C` category (including `missing-function-docstring`) is
  disabled in `pyproject.toml`.

## ALGORITHM

```
assemble_messages:
    from langchain_core.messages import HumanMessage, messages_from_dict
    result: list[Any] = list(system_messages or [])   # list[Any] keeps mypy --strict happy
    prior = [m for m in history if m.get("type") != "system"]
    result.extend(messages_from_dict(prior))
    result.append(HumanMessage(content=question))
    return result

serialize_messages:
    from langchain_core.messages import SystemMessage
    for msg in dropwhile(lambda m: isinstance(m, SystemMessage), messages):
        dump = msg.model_dump() if hasattr(msg, "model_dump") else msg.dict()
        out.append({"type": dump.pop("type", "unknown"), "data": dump})
    return out
```

`itertools.dropwhile` drops **leading** system messages only — that is the documented
contract, and it is shape-agnostic: it dumps whatever list it is handed.

The `history` filter in `assemble_messages` is deliberately **not** leading-only: loaded
history may have been written by the pre-fix agent code and contain `"system"` entries
anywhere, and leaving them in would put non-leading systems into the outgoing message list
(where `serialize_messages` would not strip them either). Filtering the raw dicts on
`type` — before `messages_from_dict` — keeps it a one-liner and behaves the same with the
conftest message stubs, which map unknown types to `HumanMessage`. Document both contracts
in the docstrings: *assemble drops history systems anywhere; serialize strips leading
systems only*.

## DATA

* `assemble_messages` → `list[BaseMessage]` (typed `list[Any]`): systems first, then
  rehydrated history, then the new `HumanMessage`.
* `serialize_messages` → `list[dict[str, Any]]`, each entry `{"type": str, "data": dict}`,
  the shape `messages_from_dict()` and `store_langchain_history()` expect.

## Tests (write first)

In `tests/llm/providers/langchain/test_langchain_messages.py`:

1. `test_assemble_orders_systems_history_then_question` — systems first, rehydrated
   history next, `HumanMessage(question)` last.
2. `test_assemble_without_systems` — `system_messages=None` → just history + question.
3. `test_assemble_with_empty_history` — `[]` history → systems + question only.
3b. `test_assemble_drops_system_messages_from_history` — a legacy-shaped history
   `[{"type": "system", ...}, {"type": "human", ...}, {"type": "ai", ...}]` → the result
   holds the fresh `system_messages` plus human + ai + question only; no rehydrated entry
   comes from the `"system"` dict. Pins the resume path for pre-fix session files.
4. `test_serialize_strips_leading_system_messages` — `[System, Human, AI]` → 2 entries,
   no `"system"` type.
5. `test_serialize_keeps_non_leading_system_message` — `[Human, System, AI]` → 3 entries;
   pins the documented "leading only" contract.
6. `test_serialize_shape_round_trips` — output feeds `messages_from_dict()` without error
   and each entry has exactly the `type` / `data` keys.
7. `test_serialize_falls_back_to_dict_method` — an object with `.dict()` but no
   `.model_dump()` is serialized via `.dict()`.
8. `test_serialize_empty_list` — `[]` → `[]`.

Message classes come from `langchain_core.messages`; the directory `conftest.py` already
substitutes lightweight stubs (with real classes, so `isinstance` works) when langchain
is absent.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1 only: create the neutral module
src/mcp_coder/llm/providers/langchain/_messages.py with assemble_messages() and
serialize_messages(), plus tests/llm/providers/langchain/test_langchain_messages.py.

Write the tests first, then the implementation. Do not modify any existing module in
this step — later steps adopt the helpers. Keep langchain_core imports deferred inside
the functions, and keep the module free of intra-package imports (circular-import
constraint explained in the summary).

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```
