# Step 3 — Gateway core: turn filter + interceptor + frame builder + deny bridge (D3/D4/D5)

**Reference:** read `pr_info/steps/summary.md` (Decisions D3, D4, D5 and the KISS notes) first.

Build the enforcement gateway and everything it needs, fully unit-tested in isolation (fake tool
objects + a fake handler — no live MCP server, no agent). This is the heart of the issue.

## WHERE
- `src/mcp_coder/icoder/permissions/gateway.py` (new) — `LangchainEnforcementGateway`, `build_legacy_frame`.
- `src/mcp_coder/llm/providers/langchain/permission_bridge.py` (new) — `build_deny_tool_message`.
- `.importlinter` — narrow `permissions_leaf_isolation` `source_modules`.
- `tests/icoder/test_permissions_gateway.py` (new).
- `tests/llm/providers/langchain/test_permission_bridge.py` (new).

## WHAT
```python
# permission_bridge.py  (provider package — allowed to touch langchain_core)
def build_deny_tool_message(text: str, name: str) -> Any:
    """Return a langchain ToolMessage(status="error") for a denied MCP call."""

# gateway.py
def build_legacy_frame(
    allowed_tools: tuple[str, ...] | None,
    enforce_skill_tools: bool,
) -> tuple[PermissionFrame | None, list[str]]:
    """Throwaway model-C frame from declared tokens (D4).

    Returns ``(frame, warnings)``. ``frame`` is ``None`` when there are no
    tokens. Per-token parse failures are **collected** into ``warnings``
    (fail-closed: the un-parseable token contributes no matcher, so it is not
    silently elevated) — the caller surfaces them (Step 4). Do NOT drop them.
    """

class LangchainEnforcementGateway:
    def __init__(self, config: PermissionConfig) -> None: ...
    def begin_turn(self, frame: PermissionFrame | None) -> None: ...
    def filter_tools(
        self, tools: list[Any], canonical_name_of: Callable[[Any], str | None]
    ) -> list[Any]: ...
    async def interceptor(
        self, request: Any, handler: Callable[[Any], Awaitable[Any]]
    ) -> Any: ...
```

## HOW
- **Imports (gateway.py):** `resolve` (resolver), `PermissionConfig`/`PermissionFrame`/`Policy` (model),
  `parse_matcher` (matcher), and `build_deny_tool_message` from the provider bridge. Annotate adapter
  request/result/handler as `Any` — do **not** import `langchain_core` or `langchain_mcp_adapters` in
  the gateway.
- **`permission_bridge.build_deny_tool_message`:** deferred `from langchain_core.messages import
  ToolMessage`; return `ToolMessage(content=text, status="error", tool_call_id="", name=name)`
  (langgraph's ToolNode overwrites `tool_call_id` with the real call id downstream).
- **`.importlinter`:** change `permissions_leaf_isolation` `source_modules` from
  `mcp_coder.icoder.permissions` to the enumerated pure modules:
  `mcp_coder.icoder.permissions.model`, `.matcher`, `.resolver`, `.loader`. This keeps the pure core a
  leaf while allowing the gateway to import the resolver + provider bridge. Run `lint-imports` to confirm.
- **Deny messages** as module constants:
  `_DENY_NEVER = "This tool is disabled by permission policy."`,
  `_DENY_ASK = "This tool requires approval — not yet available."`
- **D5 via frame base:** `build_legacy_frame` sets `base="none"` when `enforce_skill_tools` else
  `"inherit"`. `"inherit"` = elevation without narrowing (undeclared tools fall through to config);
  `"none"` = narrow undeclared to NEVER. No policy branching lives in the gateway.
- **Arg-scoped `never` stays visible (Scope requirement).** In M2 the resolver matches arg-predicate
  rules by server/tool only (`matcher.matches` ignores the predicate — parse-only until I5.4), so a
  rule like `deny mcp__git__push(command=push)` resolves the *bare* tool to `NEVER`. The turn filter
  MUST NOT hide such a tool: it hides a tool only when the decision is `NEVER` **and** the tool is
  unconditionally denied — i.e. the matched rule (`decision.matched_rule`) is absent or its
  `matcher.arg is None`. When the matched rule carries an arg predicate, the tool stays **visible** and
  is refused at call level (the interceptor still resolves `NEVER` and denies). Frame-`deny` and
  `base="none"` sandbox NEVERs have `matched_rule is None` → correctly hidden (unconditional).

## ALGORITHM
```
# build_legacy_frame  (collect parse failures — do NOT silently drop)
if not allowed_tools: return None, []
matchers, warnings = [], []
for tok in allowed_tools:
    parsed, errors = parse_matcher(tok)      # ([], [reason]) on failure (fail-closed)
    matchers.extend(parsed)
    warnings.extend(errors)                  # collected for the gateway to surface
frame = PermissionFrame(base="none" if enforce_skill_tools else "inherit", allow=tuple(matchers))
return frame, warnings

# filter_tools  (turn level; never mutates input)
# Hide ONLY unconditional NEVER. An arg-scoped never (the matched rule's
# matcher carries an arg predicate) stays visible and is refused at call level
# (predicate matching is parse-only in M2 -> the tool must not be hidden).
kept = []
for tool in tools:
    name = canonical_name_of(tool)
    if name is None:
        kept.append(tool)
        continue
    decision = resolve(name, {}, self._frame, self._config)
    if decision.policy is not Policy.NEVER:
        kept.append(tool)
        continue
    rule = decision.matched_rule
    if rule is not None and rule.matcher.arg is not None:
        kept.append(tool)   # arg-scoped never -> visible, refused at call level
return kept

# interceptor  (call level)
canonical = f"mcp__{request.server_name}__{request.name}"
policy = resolve(canonical, request.args, self._frame, self._config).policy
if policy is Policy.ALWAYS: return await handler(request)
text = _DENY_ASK if policy is Policy.AFTER_APPROVAL else _DENY_NEVER
return build_deny_tool_message(text, request.name)
```

## DATA
- `filter_tools` → a **new** `list[Any]` (never the input list); unconditional `NEVER` tools dropped,
  arg-scoped `NEVER` tools kept visible.
- `interceptor` → either the real `MCPToolCallResult` from `handler`, or a deny `ToolMessage`.
- `begin_turn` stores `frame` on `self._frame` (per-turn holder); `self._config` is immutable.
- `build_legacy_frame` → `(PermissionFrame | None, list[str] warnings)`; warnings hold every
  un-parseable token's reason (surfaced by the caller in Step 4, not dropped).

## TDD tests (write first)
Turn level (`filter_tools`):
- `never` tool dropped; `always` and `ask` kept.
- input list unmodified (identity check: original list still holds all tools → cache-safe).
- frame-elevated `never` kept: config `deny mcp__s__t`, synthetic frame `allow mcp__s__t` → tool kept.
- arg-scoped `never` kept **visible**: config `deny mcp__git__push(command=push)`, no frame → resolve
  returns `NEVER` with a `matched_rule` whose `matcher.arg is not None` → the `mcp__git__push` tool is
  kept in the filtered list (it is refused later at call level, not hidden).
- `canonical_name_of` returning `None` → tool kept (non-MCP not hidden).
Interceptor (fake `request` object with `.server_name`, `.name`, `.args`; fake async `handler`):
- `always` → `handler` awaited, its result returned (pass-through identity).
- `never` → `handler` **not** awaited; returns a `ToolMessage` with `status == "error"` and the never text.
- `ask` (config `ask`) → deny with the approval text; resolver still reported `AFTER_APPROVAL`.
- **skill-elevated `never` stays CALLABLE (frame-first, call level):** config `deny mcp__s__t`,
  synthetic frame `allow mcp__s__t`, `begin_turn(frame)` → interceptor **awaits** the real `handler`
  and returns its result (resolves `ALWAYS`), i.e. NOT denied. Covers the callable half of the
  frame-first AC (turn-level visibility is covered separately under `filter_tools`).
- canonical reconstruction: `server_name="s"`, `name="t"` resolves the rule matching `mcp__s__t`.
- two servers, same bare tool name: `mcp__a__run` denied while `mcp__b__run` allowed (disambiguation).
- `begin_turn(None)` then `begin_turn(frame)` → interceptor honours the latest frame.
Frame builder:
- `None`/empty tokens → `(None, [])`.
- tokens + `enforce_skill_tools=False` → `base=="inherit"`, matchers parsed, `warnings==[]`.
- tokens + `enforce_skill_tools=True` → `base=="none"`.
- **malformed token → warning collected, tool not elevated:** an un-parseable skill token (e.g.
  `"mcp__s__t(bad"`) yields a non-empty `warnings` list AND contributes no matcher to `frame.allow`
  (so the tool is not silently elevated to ALWAYS). Complements the Step 4 test that the warning is
  surfaced.
Bridge:
- `build_deny_tool_message("x","t")` → `ToolMessage`, `status=="error"`, `content=="x"`, `name=="t"`.

## Checks
Full quality gate green, **including `lint-imports`** (verify the narrowed leaf contract passes and
the gateway is allowed to import the resolver + provider bridge).

## Commit
`I2.3 step 3: enforcement gateway (turn filter + call interceptor + frame + deny bridge)`

## LLM prompt
> Implement Step 3 of the I2.3 plan. Read `pr_info/steps/summary.md` (D3/D4/D5 + KISS notes) and
> `pr_info/steps/step_3.md`. Following TDD, first write the gateway, bridge, and frame-builder tests,
> then implement `permission_bridge.build_deny_tool_message`, `gateway.build_legacy_frame` (returns
> `(frame, warnings)`, collecting per-token parse failures rather than dropping them), and
> `gateway.LangchainEnforcementGateway` (`begin_turn` / `filter_tools` / async `interceptor`). The
> gateway must import only the resolver/model/matcher and the provider bridge — annotate adapter types
> as `Any`; never import `langchain_core` in the gateway. Narrow the `permissions_leaf_isolation`
> import-linter contract to the pure modules. Use MCP tools only; make every check (incl. lint-imports)
> pass; one commit.
