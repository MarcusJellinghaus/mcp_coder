# Step 2 — `ApprovalBridge` Protocol + `ApprovalEngine`

**Depends on:** Step 1 (its outcome fixes the cancel mechanism).

The core of the issue: the seam Protocol in the `llm` layer and the engine in the `icoder` layer,
plus the import-linter entry that keeps the engine a leaf forever. Pure asyncio — no langchain,
no Textual, no `AppCore`.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/providers/langchain/approval_bridge.py` | **create** |
| `src/mcp_coder/icoder/permissions/approval.py` | **create** |
| `.importlinter` | **modify** — add `approval` to `permissions_leaf_isolation` |
| `tests/icoder/test_permissions_approval.py` | **create** |

## WHAT

```python
# llm/providers/langchain/approval_bridge.py  —  NO langchain import at any scope

class ApprovalBridge(Protocol):
    """Seam between the langchain consumer loop and the approval engine."""

    def attach(self, emit: Callable[[StreamEvent], None]) -> None:
        """Bind the per-turn event sink and reset per-turn state."""

    def detach(self) -> None:
        """Cancel still-pending approvals, unbind the sink, clear the registry (stale-`q` guard)."""

    def pending(self) -> int:
        """Number of approvals awaiting a human decision (read cross-thread)."""
```

```python
# icoder/permissions/approval.py

@dataclass(frozen=True)
class ApprovalDecision:
    outcome: Literal["allow", "deny"]
    scope: Literal["once", "session", "persist"] = "once"
    reason: str | None = None                     # deny text override; None -> gateway's R11 wording
    def __post_init__(self) -> None: ...          # deny is once-only in v1 (§10.2 D-K)

class ApprovalEngine:
    def attach(self, emit: Callable[[StreamEvent], None]) -> None: ...
    def detach(self) -> None: ...
    def pending(self) -> int: ...
    def is_attached(self) -> bool: ...
    async def request_approval(
        self, *, tool_name: str, args: Mapping[str, object], source: str
    ) -> ApprovalDecision: ...                    # agent loop only
    def resolve_pending(self, approval_id: str, decision: ApprovalDecision) -> None: ...  # UI thread
    def cancel_all(self) -> None: ...                                                     # UI thread
    def pending_ids(self) -> tuple[str, ...]: ...
    @property
    def cancelled(self) -> bool: ...
```

## HOW

* **Typing-only downward import.** In `approval.py` import `ApprovalBridge` under
  `if TYPE_CHECKING:` and prove conformance in the test with
  `bridge: ApprovalBridge = ApprovalEngine()` (mypy checks it). A runtime import would eagerly
  execute the langchain package `__init__` for every importer of `icoder.permissions`.
  Import-linter still sees the edge (grimp is AST-based) — and it is legal: importing a
  *submodule* creates no edge to its parent package, and `approval_bridge` imports no
  `langchain_*`.
* **`.importlinter`:** add `mcp_coder.icoder.permissions.approval` to the
  `permissions_leaf_isolation` `source_modules` list. Add nothing else yet — the
  `layered_architecture` entry belongs in Step 7, where the CLI import actually appears.
* **No lock, no deque, no counter** (summary §2.2). Document *why* in the class docstring, and
  document it **accurately** — the registry is mutated on the agent loop in the normal case
  (`resolve_pending` / `cancel_all` only `call_soon_threadsafe`), but three members are touched
  off that loop and the docstring must name them: `attach()` / `detach()` mutate `_pending`,
  `_emit`, `_loop` (and `_cancelled`, on `attach`) from the **consumer thread**, and `detach()`
  follows a `thread.join(timeout=5)` that **may expire with the agent loop still live**;
  `cancel_all()` sets `_cancelled` from the **Textual thread**; `pending()` is a cross-thread
  `len()` read. Each is one attribute rebind or one `len()`, atomic under the GIL — hence no
  lock — but the `_emit is None` guard and the cancel-then-clear `detach()` below are what make
  that safe. Do **not** write "everything runs single-threaded on the agent loop".
* **Carry the FINDINGS rationale as docstrings** (D9 handoff): `get_running_loop()` inside the
  coroutine and never a build-time handle (§2); why the direct cancel channel exists (§4); why
  `detach()` clearing the registry is load-bearing — `asyncio.run` is called per turn so the loop
  object differs every turn (§5 stale-`q`).
* Record the **R3 mechanism deviation** in the class docstring (guarantee preserved, lock removed).

## ALGORITHM

```python
async def request_approval(self, *, tool_name, args, source):
    if self._cancelled or self._emit is None:
        return ApprovalDecision("deny", "once")     # fail closed, never await
    self._loop = asyncio.get_running_loop()          # FINDINGS §2 — inside the coroutine
    approval_id = uuid4().hex
    fut = self._loop.create_future()
    self._pending[approval_id] = _PendingApproval(fut, self._payload(approval_id, ...))
    if len(self._pending) == 1:                      # only the front entry is ever emitted
        self._emit_front()
    try:
        return await fut                             # CancelledError propagates to the gateway
    finally:
        self._pending.pop(approval_id, None)
        if not self._cancelled and self._emit is not None:
            self._emit_front()                       # promote next, FIFO by arrival order
```

The `self._emit is not None` half of that guard is not defensive padding: `detach()` runs on the
consumer thread after a `thread.join(timeout=5)` that can expire while this coroutine is still
alive, so the sink may already be gone when the `finally` runs.

```python
def resolve_pending(self, approval_id, decision):     # Textual thread
    entry, loop = self._pending.get(approval_id), self._loop
    if entry and loop:
        loop.call_soon_threadsafe(_set_if_pending, entry.future, decision)

def cancel_all(self):                                 # Textual thread
    self._cancelled = True
    if self._loop:
        self._loop.call_soon_threadsafe(self._cancel_all_on_loop)   # iterate ON the loop

def detach(self):                                     # consumer thread
    # Cancel BEFORE clearing: after the clear nothing can reach these futures again,
    # and an interceptor parked on one keeps the daemon agent thread alive for the
    # rest of the process (summary §2.3/§2.10 — GeneratorExit *is* reachable while
    # an approval is pending, and the 5s join then expires).
    loop = self._loop
    if loop is not None:
        for entry in list(self._pending.values()):
            loop.call_soon_threadsafe(entry.future.cancel)
    self._pending.clear()
    self._emit = None
    self._loop = None                                 # `_cancelled` survives (summary §2.8)
```

## DATA

* `_PendingApproval = NamedTuple("_PendingApproval", [("future", asyncio.Future[ApprovalDecision]),
  ("payload", StreamEvent)])`.
* Emitted payload (JSON-safe — `source` is a **plain string**, never a `Decision.Source`
  dataclass):
  `{"type": "approval_request", "approval_id": str, "tool_name": str, "args": dict, "source": str}`
* `pending_ids()` returns arrival order (insertion precedes any `await`), so FIFO assertions are
  non-circular.
* State lifecycle: `attach()` clears `_pending`, `_loop`, **and `_cancelled`**; `detach()`
  **cancels** every still-pending future (via `call_soon_threadsafe`) and then clears `_pending`,
  `_emit`, `_loop`, but **keeps `_cancelled`** — `AppCore.stream_llm` reads it *after*
  `_ask_agent_stream`'s `finally` has already detached (summary §2.8). Assert this in a test.
* `ApprovalDecision.__post_init__` raises `ValueError` for `deny` + `session|persist`.
* `ApprovalDecision.reason` is an optional deny-text override. The engine never reads it; it is
  carried through to the gateway, which uses it in place of `_DENY_USER` (Step 4). Step 8's
  interim auto-deny is its only producer until #1046. `reason` on an `allow` is ignored.

## TESTS (write first)

1. Allow: `request_approval` returns the decision resolved from another thread.
2. Deny: same, with `ApprovalDecision("deny", "once")`.
3. Two concurrent asks: **exactly one** `approval_request` emitted; answering #1 emits #2;
   each future resolves via its own `approval_id`, no cross-wiring; `pending_ids()` order equals
   arrival order.
4. `pending()` reflects the registry and is `> 0` from before the first emit until the answer.
5. `cancel_all()` → every awaiting coroutine raises `CancelledError`; **no** further
   `approval_request` is emitted for a queued sibling; `cancelled` is `True`.
6. `detach()` clears the registry; `attach()` resets `cancelled`; `detach()` does **not**.
7. **`detach()` with an approval still pending cancels it:** the awaiting coroutine raises
   `CancelledError` (it does not hang), and the registry is empty afterwards. This is the
   turn-ends-while-pending case from summary §2.3 — without it the coroutine parks forever on a
   future no registry can reach.
8. Unattached engine → `request_approval` returns a deny immediately and never awaits.
9. `ApprovalDecision("deny", "session")` raises `ValueError`.
10. `ApprovalDecision("deny", "once", reason="…")` round-trips its `reason` back to the caller of
    `request_approval`.
11. Static conformance: `bridge: ApprovalBridge = ApprovalEngine()`.

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check`, **and `run_lint_imports_check`** — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (especially §2.1–§2.3 and §2.8) and `pr_info/steps/step_2.md`,
> then implement Step 2 only.
>
> Create `src/mcp_coder/llm/providers/langchain/approval_bridge.py` (the `ApprovalBridge` Protocol —
> **no langchain import at any scope**) and `src/mcp_coder/icoder/permissions/approval.py`
> (`ApprovalDecision` + `ApprovalEngine`). Add `mcp_coder.icoder.permissions.approval` to the
> `permissions_leaf_isolation` contract in `.importlinter`. Write
> `tests/icoder/test_permissions_approval.py` first, covering all eleven cases listed in the step.
>
> The engine holds **one insertion-ordered dict** — no `asyncio.Lock`, no `deque`, no separate
> counter. Follow the pseudocode in the step exactly, including the `self._emit is not None` guard
> in `request_approval`'s `finally` and the **cancel-then-clear** `detach()`. Document in the class
> docstring: why no lock is needed **and which members are mutated off the agent loop**
> (`attach`/`detach` on the consumer thread after a join that may expire, `cancel_all`'s
> `_cancelled` on the Textual thread, `pending()` read cross-thread) — do not claim everything runs
> single-threaded on the agent loop; why the loop handle comes from `get_running_loop()` inside the
> coroutine; why the direct cancel channel exists; why `detach()` must cancel and then clear the
> registry; and that this preserves R3's guarantee while dropping its lock mechanism.
>
> `approval.py` must import `ApprovalBridge` only under `TYPE_CHECKING`, and must never import
> `permission_bridge`, `langchain_core`, `textual`, or anything from `icoder.core` / `icoder.ui` /
> `icoder.services`.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` and
> `run_lint_imports_check` all green, then one commit.
