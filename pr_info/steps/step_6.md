# Step 6 — Gateway: real `AFTER_APPROVAL` branch + runtime-rule store

**Depends on:** Step 4 (engine), Step 5 (runtime stage).

Replaces I2.3's `AFTER_APPROVAL` → deny placeholder with the real branch, and adds the
runtime-rules store that I3.3/#1046 will write to.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/icoder/permissions/gateway.py` | **modify** |
| `tests/icoder/test_permissions_gateway.py` | **modify** |

## WHAT

```python
_DENY_NEVER = "This tool is disabled by permission policy."           # unchanged
_DENY_ASK = "This tool requires approval — not yet available."        # REPURPOSED: fail-closed fallback
_DENY_USER = (                        # R11 — canonical wording; used unless the decision
                                      # carries its own `reason` (see the AFTER_APPROVAL branch)
    "Tool call denied by the user. Do not retry this call — choose a "
    "different approach, or ask the user what they would prefer."
)

class LangchainEnforcementGateway:
    def __init__(
        self,
        config: PermissionConfig,
        approval_engine: ApprovalEngine | None = None,
    ) -> None: ...

    def add_runtime_rule(self, rule: Rule) -> None:
        """Append a rule to the in-memory ``runtime`` layer (I3.3 writes; engine never does)."""

    async def interceptor(self, request: Any, handler: ...) -> Any: ...   # rewritten branch

def _source_label(source: Source) -> str:
    """Flatten a Decision.Source to a JSON-safe plain string for the event payload."""
```

## HOW

* `interceptor` must keep the **whole `Decision`**, not just `.policy` — R15 branches on
  `isinstance(decision.source, Degraded)`.
* `add_runtime_rule` is `self._config = replace(self._config, rules=self._config.rules + (rule,))`.
  `PermissionConfig` is frozen; the rebind is atomic under the GIL, so **no lock**. Both
  `filter_tools` and `interceptor` already read `self._config` live — verify they never capture it
  into a local across calls.
* The deny `ToolMessage` is built **here** via `build_deny_tool_message(text, request.name,
  tool_call_id)`, never in the engine (R6 — the engine must not import `permission_bridge`).
* `CancelledError` from `engine.request_approval` must **propagate**, not be caught: it unwinds the
  turn. Note that in a comment so nobody adds a `try/except` later.
* `_source_label`: `Layer` → `.name`; `Default()` → `"default"`; `Frame()` → `"frame"`.
  `Degraded` cannot reach the emit (R15) — assert that with a comment, not a branch.
* Update the class/module docstring: the `AFTER_APPROVAL` line currently says it returns a deny.

## ALGORITHM

```python
canonical = f"mcp__{request.server_name}__{request.name}"
decision = resolve(canonical, request.args, self._frame, self._config)
tool_call_id = getattr(getattr(request, "runtime", None), "tool_call_id", None) or ""

if decision.policy is Policy.ALWAYS:
    return await handler(request)
if decision.policy is Policy.NEVER:
    return build_deny_tool_message(_DENY_NEVER, request.name, tool_call_id)

# AFTER_APPROVAL
if isinstance(decision.source, Degraded):                       # R15 — no prompt, ever
    return build_deny_tool_message(_DENY_NEVER, request.name, tool_call_id)
if self._engine is None or not self._engine.is_attached():      # fail closed, never await
    return build_deny_tool_message(_DENY_ASK, request.name, tool_call_id)
approved = await self._engine.request_approval(                 # CancelledError propagates
    tool_name=canonical, args=request.args, source=_source_label(decision.source)
)
if approved.outcome == "allow":
    return await handler(request)
# `reason` lets the answering side override the wording. Step 9's interim UI
# auto-deny and the engine's own fail-closed deny both use it, so a call nobody
# was asked about is not reported to the model as a user denial.
return build_deny_tool_message(approved.reason or _DENY_USER, request.name, tool_call_id)
```

## DATA

* Returns unchanged in shape: the real handler result, or a `ToolMessage(status="error")` carrying
  the **real** `tool_call_id` (the empty-id wedge is FINDINGS §10; #1118 fixed the source).
* `add_runtime_rule` returns `None` and mutates one attribute.
* A rule added mid-turn **is** visible to later call-level `resolve()`s in the same turn; it
  **cannot** un-hide a `never` tool mid-turn, because `filter_tools` is a turn-start snapshot.
  State that in the `add_runtime_rule` docstring.

## TESTS (write first)

Extend the existing fake-request / fake-handler style already in the file (it stubs the deny
bridge via an autouse fixture, so no `langchain_core` is needed).

1. `AFTER_APPROVAL` + engine returning **allow** → the real handler is awaited.
2. `AFTER_APPROVAL` + engine returning **deny** → `ToolMessage` with `_DENY_USER` and the real
   `tool_call_id`; the handler is **not** awaited; nothing raises.
2b. `AFTER_APPROVAL` + a deny carrying `reason="…"` → the `ToolMessage` uses that text, not
   `_DENY_USER` (Step 9's interim auto-deny and the engine's fail-closed deny both depend on it).
3. `AFTER_APPROVAL` + engine raising `CancelledError` → it propagates out of `interceptor`.
4. **Degraded config** → deny, and `request_approval` was **never called** (assert on a spy).
5. **No engine** and **engine not attached** → `_DENY_ASK` deny with the real `tool_call_id`, and
   no `await` on any future (two separate cases).
6. `NEVER` and `ALWAYS` paths unchanged (existing tests stay green).
7. `add_runtime_rule` → a subsequent `interceptor` call for the same tool resolves `ALWAYS`
   (the R14 + store combination; this is the engine-free half of the `scope=session` criterion).
8. `_source_label` maps `Layer("project")`/`Default()`/`Frame()` to `"project"`/`"default"`/`"frame"`.

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check`, `run_lint_imports_check` — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.5, §2.6) and `pr_info/steps/step_6.md`, then implement
> Step 6 only.
>
> Rewrite the `AFTER_APPROVAL` branch of
> `src/mcp_coder/icoder/permissions/gateway.py::LangchainEnforcementGateway.interceptor` per the
> step's pseudocode: keep the whole `Decision` (not just `.policy`), deny outright when
> `decision.source` is `Degraded` **without emitting an approval request**, fail closed with
> `_DENY_ASK` when no engine is attached (never awaiting a Future nobody will resolve), otherwise
> await `engine.request_approval(...)` and allow, or deny with `decision.reason` when the decision
> carries one and the canonical R11 wording otherwise. Let
> `CancelledError` propagate. Add `add_runtime_rule(rule)` using `dataclasses.replace`, and a
> `_source_label` helper that flattens `Decision.Source` to a plain JSON-safe string.
>
> Add an `approval_engine: ApprovalEngine | None = None` constructor parameter. The deny
> `ToolMessage` is constructed here, never in the engine.
>
> Write the nine test cases listed in the step first (including the `reason`-override case),
> extending
> `tests/icoder/test_permissions_gateway.py` in its existing style (the autouse fixture already
> stubs the deny bridge). Update the module/class docstrings, which currently say
> `AFTER_APPROVAL` returns a deny.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` and
> `run_lint_imports_check` all green, then one commit.
