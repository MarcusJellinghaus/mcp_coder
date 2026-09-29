# Step 2 — `permissions/expand.py`: the pure token expander

Read [summary.md](./summary.md) §2 (the module) and §3 (cycles) first.

Pure, self-contained, no caller yet. Landing it alone keeps step 3 (the loader restructure) small.

## WHERE

- `src/mcp_coder/icoder/permissions/expand.py` (create)
- `src/mcp_coder/icoder/permissions/__init__.py` (modify — export `expand`)
- `.importlinter` (modify — add the module to both permission contracts)
- `tests/icoder/test_permissions_expand.py` (create)

## WHAT

```python
def is_ref(token: str) -> bool:
    """Return True if ``token`` is a ``@group`` reference (whitespace-tolerant)."""

def ref_name(token: str) -> str:
    """Return the bare group name of a ``@ref`` token (no leading ``@``)."""

def expand(
    token: str,
    groups: Mapping[str, Sequence[str]],
) -> tuple[list[Matcher], list[str]]:
    """Expand one token into matchers, resolving ``@group`` refs transitively."""

def _expand_ref(
    token: str,
    groups: Mapping[str, Sequence[str]],
    visited: frozenset[str],
) -> tuple[list[Matcher], list[str]]:
    """Recursive worker: expand one ``@ref`` under a visited-name set."""
```

## HOW

- **Single-token** API (a simplification over the issue's `expand(tokens, …)` sketch): both callers —
  the loader's per-rule loop and I4.2's runtime grant — already work one token at a time, and the
  loader needs per-token granularity anyway for D11 and for origin synthesis.
- `groups` is the **raw-token-valued** merged map, i.e. `Mapping[str, Sequence[str]]`, *not*
  `PermissionConfig.groups`. This is what allows transitive expansion.
- Imports: `parse_matcher` from `.matcher`, `Matcher` from `.model`. Nothing else — the module must
  stay pure and leaf.
- Errors are **pathless** (`"unknown group reference '@git'"`); the loader adds `f"{path}: {err}"`,
  matching today's `_parse_matchers` convention. Do not log here.
- `is_ref` / `ref_name` become the single home for the `@` convention. Steps 3 and 5 replace the
  duplicated `token.strip().startswith("@")` / `token.startswith("@")` checks in `loader.py` and
  `skill_frame.py` with these.
- `permissions/__init__.py`: add `expand` to the imports and `__all__` (vulture treats `__all__`
  membership as usage, so the not-yet-called function does not trip it).
- `.importlinter`: add `mcp_coder.icoder.permissions.expand` to `source_modules` of **both**
  `permissions_leaf_isolation` and `permissions_core_purity`.

## ALGORITHM

```
expand(token, groups):
    if not is_ref(token):          return parse_matcher(token)        # leaf, as today
    matchers, errors = _expand_ref(token, groups, visited=frozenset())
    if not errors and not matchers:                                   # D3 + D4 in one check
        errors = [f"group reference {token!r} resolves to no tools (empty or cyclic)"]
    return matchers, errors

_expand_ref(token, groups, visited):
    name = ref_name(token)
    if name in visited:            return [], []                      # contributes once; cycle-safe
    if name not in groups:         return [], [f"unknown group reference '@{name}'"]
    for member in groups[name]:                                       # recurse refs, parse leaves
        sub = _expand_ref(member, groups, visited | {name}) if is_ref(member) else parse_matcher(member)
        accumulate matchers and errors
    return matchers, errors
```

Note the asymmetry that step 3's tests pin: an **unknown name is an error at any depth**, while
**emptiness is only checked on the top-level result** — so a nested ref to a defined-but-empty group
does not poison a sibling that resolved.

## DATA

- Returns `(matchers, errors)`; on any error the caller treats the whole token as granting nothing
  (fail-closed), consistent with `parse_matcher`.
- A value-set token still expands to N matchers via `parse_matcher` — refs and value-sets compose.
- No `origin` stamping here; that is the loader's 3 lines in step 3.

## Tests (write first)

`tests/icoder/test_permissions_expand.py`, all pure (a plain dict as `groups`):

1. Non-ref token delegates to `parse_matcher` (one matcher, no errors); a malformed non-ref token
   returns its `parse_matcher` error unchanged.
2. `@git` with `{"git": ["mcp__git__status", "mcp__git__log"]}` → 2 matchers, no errors.
3. **Transitive**: `{"write": ["@read", "mcp__git__commit"], "read": ["mcp__git__log"]}` → `@write`
   yields both, no errors.
4. **Unknown ref** → `([], [1 error])`, error names `@nope`.
5. **Unknown nested ref** → error surfaces from depth; assert the test terminates and the error names
   the missing name.
6. **Cycle** `{"a": ["@b"], "b": ["@a"]}` → terminates, `matchers == []`, one "resolves to no tools"
   error (AC: "cyclic `@ref` resolves without hanging").
7. **Diamond** `{"a": ["@c", "@b"], "b": ["@c"], "c": ["mcp__fs__read"]}` → `mcp__fs__read` appears
   **once** (D4: an already-visited member contributes once).
8. Defined-but-empty group referenced directly → one "resolves to no tools" error (the accepted edge,
   summary §3).
9. Nested empty group does **not** error when a sibling member resolved (the asymmetry above).
10. Whitespace tolerance: `" @git"` resolves exactly like `"@git"`.
11. A value-set member inside a group expands to N matchers.
12. `is_ref` / `ref_name`: `"@git"` → `True`/`"git"`; `" @git"` → `True`/`"git"`;
    `"mcp__git__log"` → `False`.

## LLM prompt

> Implement **step 2** of `pr_info/steps/summary.md` as described in `pr_info/steps/step_2.md`.
> Read the summary first (§2 and §3) for the settled decisions D3/D4 and for why the API is
> single-token.
>
> Test-driven: write `tests/icoder/test_permissions_expand.py` with the twelve cases listed, watch
> them fail, then implement `src/mcp_coder/icoder/permissions/expand.py`.
>
> Keep the module pure: import only `parse_matcher` and `Matcher`, return errors as data, never log,
> never touch the filesystem. Do **not** build an explicit cycle detector — the visited-set plus the
> single "expands to zero matchers" check is the whole mechanism. Do not add a second public
> function; origin stamping belongs to step 3.
>
> Also export `expand` from `permissions/__init__.py` and add
> `mcp_coder.icoder.permissions.expand` to both permission contracts in `.importlinter`.
>
> Then run the checks listed at the end of the summary, including `run_lint_imports_check`. One commit.
