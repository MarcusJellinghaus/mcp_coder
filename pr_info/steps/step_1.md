# Step 1 — Carry the real `tool_call_id` through both deny branches

**Goal:** the deny `ToolMessage` returned for `NEVER` and `AFTER_APPROVAL` carries the
tool_call id the model emitted, sourced from the langgraph runtime already present on the
adapter request.

**One commit:** tests + implementation + all checks green. The bridge signature change and
its two call sites must land together (a required third parameter breaks the caller
otherwise).

---

## WHERE

| Path | Role |
|---|---|
| `tests/llm/providers/langchain/test_permission_bridge.py` | unit — bridge shape (write first) |
| `tests/icoder/test_permissions_gateway.py` | unit — gateway sourcing (write first) |
| `src/mcp_coder/llm/providers/langchain/permission_bridge.py` | production — the langchain shape |
| `src/mcp_coder/icoder/permissions/gateway.py` | production — the pure enforcement seam |
| `spikes/i3-1-approval/tier_c.py` | call-site follow-through (one line) |

---

## WHAT — signatures

```python
# src/mcp_coder/llm/providers/langchain/permission_bridge.py
def build_deny_tool_message(text: str, name: str, tool_call_id: str) -> Any: ...

# src/mcp_coder/icoder/permissions/gateway.py  (unchanged signature)
async def interceptor(self, request: Any, handler: Callable[[Any], Awaitable[Any]]) -> Any: ...
```

Only `build_deny_tool_message` changes shape: a third **required** positional parameter.
Required — not defaulted to `""` — so the old 2-arg call is a visible regression signal.

---

## HOW — integration points

* No new imports in either production module. The gateway must **not** import
  `langchain_core`, `langgraph` or `langchain_mcp_adapters`; it reads the id with plain
  `getattr` chaining and `request` stays typed `Any`. The
  `langchain_library_isolation` import contract enforces this — `run_lint_imports_check`
  must stay green.
* The bridge keeps its function-local `from langchain_core.messages import ToolMessage`.
* `tests/icoder/test_permissions_gateway.py` stubs the bridge via the existing autouse
  `_fake_deny_bridge` monkeypatch fixture; widen that stub to 3 args so the gateway tests
  still need no `langchain_core`.

---

## ALGORITHM — gateway deny path

```
policy = resolve(canonical, request.args, frame, config).policy
if policy is ALWAYS:            return await handler(request)
text = _DENY_ASK if policy is AFTER_APPROVAL else _DENY_NEVER
runtime = getattr(request, "runtime", None)          # absent on non-graph/old adapters
tool_call_id = getattr(runtime, "tool_call_id", None) or ""   # None outside a graph
return build_deny_tool_message(text, request.name, tool_call_id)
```

Written as one expression to match the module's style (black wraps it):

```python
        tool_call_id = (
            getattr(getattr(request, "runtime", None), "tool_call_id", None) or ""
        )
        return build_deny_tool_message(text, request.name, tool_call_id)
```

---

## DATA — return values

* `build_deny_tool_message(...)` -> `ToolMessage(content=text, status="error",
  tool_call_id=tool_call_id, name=name)`.
* `interceptor(...)` -> unchanged contract: the real handler result for `ALWAYS`, else that
  deny `ToolMessage`.
* Fallback: no `runtime` attribute, `runtime is None`, or `tool_call_id is None` -> `""`
  (exactly today's behaviour outside a graph).

---

## TDD order

### 1. `tests/llm/providers/langchain/test_permission_bridge.py` (red)

* **Module docstring (D4):** delete the false parenthetical *"(langgraph's `ToolNode` fills
  in the real `tool_call_id` downstream)"*; replace with a statement that the deny message
  carries the id of the tool call it denies.
* Update both existing tests to the 3-arg call:
  `build_deny_tool_message("x", "t", "call_1")`.
* Add:

```python
def test_build_deny_tool_message_carries_tool_call_id() -> None:
    """The deny message keeps the tool_call id it was given (history stays paired)."""
    msg = build_deny_tool_message("denied", "some_tool", "call_1")

    assert msg.tool_call_id == "call_1"
```

### 2. `tests/icoder/test_permissions_gateway.py` (red)

* `_request` gains a runtime carrying the id:

```python
def _request(
    server_name: str,
    name: str,
    args: dict[str, Any] | None = None,
    tool_call_id: str = "call_1",
) -> Any:
    """Build a fake adapter request, incl. the langgraph runtime ToolNode injects."""
    return SimpleNamespace(
        server_name=server_name,
        name=name,
        args=args or {},
        runtime=SimpleNamespace(tool_call_id=tool_call_id),
    )
```

* Widen the autouse `_fake_deny_bridge` stub and let it mirror the id back, so no separate
  capture list is needed (update its docstring: the gateway must hand the bridge the
  correct text **and** tool_call id):

```python
    def _fake(text: str, name: str, tool_call_id: str) -> Any:
        return SimpleNamespace(
            content=text,
            status="error",
            name=name,
            tool_call_id=tool_call_id,
            type="tool",
        )
```

* Add three tests (the first two fail against today's 2-arg call — the regression signal):

```python
async def test_interceptor_never_carries_tool_call_id() -> None:
    """A ``never`` denial carries the emitted tool_call id (history stays paired)."""
    # config NEVER -> await interceptor(_request("s", "t", tool_call_id="call_7"), handler)
    # assert result.tool_call_id == "call_7"

async def test_interceptor_ask_carries_tool_call_id() -> None:
    """An ``ask`` denial carries the emitted id too (same shared bridge call)."""

async def test_interceptor_deny_without_runtime_uses_empty_id() -> None:
    """No ``runtime`` on the request (outside a graph) -> the id falls back to ``""``."""
    # request built inline WITHOUT a runtime attribute:
    #   SimpleNamespace(server_name="s", name="t", args={})
    # assert result.tool_call_id == ""
```

The existing `test_interceptor_never_*` / `test_interceptor_ask_*` tests keep working
through the widened stub; no other change to them.

### 3. Production (green)

* `permission_bridge.py`: add the parameter, set it on the `ToolMessage`, and rewrite the
  `Args:`/`Returns:` docstring — **the "ToolNode overwrites it downstream" sentence must be
  gone** (D4). Document `tool_call_id` as *the id of the model's tool call being denied, so
  the deny message stays paired with it in the agent's history*.
* `gateway.py`: apply the ALGORITHM above. Extend the `interceptor` docstring's `Args:`
  entry for `request` to mention `.runtime` (carrying the emitted `tool_call_id` inside a
  langgraph run). Leave the module docstring alone — it stays accurate.

### 4. `spikes/i3-1-approval/tier_c.py` (call-site follow-through)

One line in `InterceptorGate.interceptor`:

```python
            return build_deny_tool_message(_DENY_TEXT, request.name, "")
```

Replace the two stale comment lines above it (*"request exposes only .server_name / .name /
.args, so there is no tool_call_id to derive"* — now known false) with a single accurate
note: the explicit `""` keeps this frozen spike run byte-identical to the pre-#1118
behaviour it recorded. Do **not** touch `FINDINGS.md`.

---

## Checks (all via MCP tools, all must pass)

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_ruff_check(extra_args=["--preview"])
mcp__mcp-tools-py__run_lint_imports_check
```

Ruff runs the `D`/`DOC` rules in preview mode: the new `tool_call_id` parameter needs an
`Args:` entry in the bridge docstring or `DOC` fails. Run `./tools/format_all.sh` before
committing.

---

## Done when

* `build_deny_tool_message` sets a caller-supplied `tool_call_id`; no docstring anywhere
  claims `ToolNode` fills it in.
* Both deny branches pass the id sourced from `request.runtime.tool_call_id`, `""` when
  absent.
* All five checks green; `lint-imports` confirms the gateway still imports no
  `langchain_core`.

---

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`, then implement step 1.
>
> Use MCP tools exclusively for file access and checks (see `.claude/CLAUDE.md`) — never
> `Read`/`Write`/`Edit`, never `Bash` for pylint/pytest/mypy.
>
> Work TDD: first update `tests/llm/providers/langchain/test_permission_bridge.py` and
> `tests/icoder/test_permissions_gateway.py` exactly as the step describes and confirm the
> new gateway tests fail against the current 2-arg `build_deny_tool_message` call (that
> failure is the regression signal). Then apply the production change to
> `permission_bridge.py` and `gateway.py`, plus the one-line call-site update in
> `spikes/i3-1-approval/tier_c.py`.
>
> Constraints: `gateway.py` must not import `langchain_core`, `langgraph` or
> `langchain_mcp_adapters` — read the id with plain `getattr` chaining and keep `request`
> typed `Any`. The third bridge parameter is required, not defaulted. Delete the false
> "ToolNode overwrites it downstream" claim from both the bridge docstring and the bridge
> test-module docstring. Do not edit `spikes/i3-1-approval/FINDINGS.md`.
>
> Run all five checks listed in the step and fix everything they report. Then
> `./tools/format_all.sh` and make exactly one commit.
