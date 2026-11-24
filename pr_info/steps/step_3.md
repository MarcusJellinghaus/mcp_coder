# Step 3: `verify` rows for declared toolkit depths

Read `pr_info/steps/summary.md` first (section "Design", part 3).

## LLM prompt

> Implement step 3 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_3.md`. Write the tests first, then add `can_request` to
> `src/mcp_coder/utils/toolkit_runner.py` and the declared-depth rows to
> `src/mcp_coder/cli/commands/verify_toolkit_rows.py`. Run pylint, pytest (unit
> markers excluded as in CLAUDE.md) and mypy. All must pass. Then format and commit as one commit.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py`
- `src/mcp_coder/cli/commands/verify_toolkit_rows.py`
- `tests/utils/test_toolkit_runner.py`
- `tests/cli/commands/test_verify_toolkit_rows.py`

## WHAT

`toolkit_runner.py`:

```python
def can_request(action: str, depth: str) -> bool:
    """Whether any binding entry may request ``action@depth``."""
```

`verify_toolkit_rows.py`:

```python
_COMMAND_TOOLKIT = "command"  # the toolkit whose depths the user writes

def _ran_by(
    loaded: LoadedToolkit, requests: dict[tuple[str, str], list[str]]
) -> dict[tuple[str, str], list[str]]:
    """Map each depth that runs to the entries whose requests resolve to it."""

def _declared_row(
    action: str, depth: str,
    ran: dict[tuple[str, str], list[str]],
    ran_any: dict[tuple[str, str], list[str]],
    command: bool, symbols: dict[str, str], indent: int,
) -> Row | None:
    """Row for one declared depth; None for an unrequested depth of other toolkits."""
```

`toolkit_rows` (changed): adds `_declared_row` rows to each action group and builds groups for more actions. Update its docstring and the module docstring.

## HOW

- `verify_toolkit_rows.py` imports `can_request` next to `resolve_depth`.
- `_requests` and `_depth_row` stay as they are.
- `verify()` still runs only for the **requested** actions (today's `actions` list).
- The group loop runs over `requested actions + declared actions` (deduplicated, requested first). Declared actions are added only when `loaded.name == _COMMAND_TOOLKIT`.
- In each group: verify items, then the existing `_depth_row` rows, then one `_declared_row` per depth in `loaded.info.actions.get(action, [])`, in declaration order.
- Labels use `action@depth`, like the existing request rows. That avoids clashing with verify items named `check.quick`.
- Warnings don't change the return value (only `failure` rows do).

## ALGORITHM

```
can_request: return any(action in allowed and f"{action}@{depth}" not in _FORBIDDEN_REQUESTS.get(e, ())
                        for e, allowed in _ALLOWED_ACTIONS.items())
_ran_by:     for (action, depth), entries in requests: r = resolve_depth(declared.get(action, []), depth)
             if r: add entries (dedup, first-seen order) to out[(action, r)]
toolkit_rows: ran = _ran_by(loaded, requests); ran_any = _ran_by(loaded, _requests(bindings, True))
_declared_row: if in ran → ok "requested by a, b"; elif not command → None
               elif not can_request → warn "no binding can request it; delete it"
               elif in ran_any → warn "unused while format_code is off"
               else → warn "not requested by any binding; delete it or add it to a binding"
```

## DATA

- `ran` / `ran_any`: `dict[tuple[str, str], list[str]]`, mapping `(action, resolved depth)` to binding entries.
- Rows: `Row(f"{action}@{depth}", symbols[...], message, indent + 4, wrap=True)`.

## Tests (write first)

`tests/utils/test_toolkit_runner.py`:

- `can_request("format", "check")` is False.
- `can_request("format", "apply")`, `("check", "full")` and `("test", "mutation")` are True.
- `can_request("lint", "quick")` is False.

`tests/cli/commands/test_verify_toolkit_rows.py`. Use `CommandToolkit` with default bindings and `format_code` on, declaring `check.quick`, `check.standard`, `check.full`, `test.quick`, `test.unattended`, `test.mutation`, `format.apply` and `format.check`. Patch `verify_toolkit` as the existing tests do. Assert:

- ok rows:
  - `check@quick` → `implement_task`;
  - `check@standard` → `implement_final, rebase, rebase_automated`;
  - `test@quick` → `implement_final, rebase` (rebase reaches it by fallback from `test@standard`);
  - `test@unattended` → `rebase_automated`;
  - `format@apply` → `commit`.
- Warnings: `check@full` and `test@mutation` ("not requested by any binding…"); `format@check` ("no binding can request it; delete it").
- The existing fallback warning `test@standard` ("not declared; runs quick") is unchanged.
- `format_code` off: `format@apply` gets only "unused while format_code is off". `format@check` still gets "no binding can request it". A `format` group exists even though no binding requests `format`.
- A non-command fake toolkit (the existing `_toolkit(...)` helper) declaring an extra `check.full` gets an ok row per requested depth and no warning row.
- Adapt existing tests that assert exact row lists or the absence of a group: requested and declared depths now always add an ok row.
