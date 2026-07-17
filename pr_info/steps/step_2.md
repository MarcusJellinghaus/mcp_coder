# Step 2 — Matcher engine (parse + rank + match)

**Ref:** `pr_info/steps/summary.md`. One commit: tests + implementation + all checks
green. Depends on Step 1.

## WHERE
- Create `src/mcp_coder/icoder/permissions/matcher.py`
- Create `tests/icoder/test_permissions_matcher.py`
- (optional) extend `__init__.py` exports with `parse_matcher`, `specificity`,
  `matches`.

## WHAT (matcher.py — pure string logic; imports model only)

```python
def parse_matcher(text: str) -> tuple[list[Matcher], list[str]]:
    """Parse a matcher string into 1+ Matchers, or return errors.

    Value-sets expand into N exact matchers. Returns (matchers, errors);
    on any error, matchers is [] (fail-closed) — the caller emits the warning.
    """

def specificity(m: Matcher) -> Specificity:
    """(arg_rank, concrete_tool, concrete_server); each 0 or 1."""

def matches(m: Matcher, canonical_tool: str) -> bool:
    """True if m matches a canonical 'mcp__server__tool' name (wildcards honoured).

    The arg predicate is NOT evaluated in M2.
    """
```

## HOW
- Import `Matcher`, `ArgPredicate`, `Specificity`, `WILDCARD` from `.model`.
- Grammar (server/tool granularity): `mcp__<server>__<tool>` where `<server>` and
  `<tool>` may be `*`. Optional single arg predicate: `<...>(<name>=<value>)`.
- Errors are returned as data (never logged). Fail-closed cases (each -> `([], [msg])`):
  - malformed token (doesn't match `mcp__server__tool`);
  - **>1 arg predicate** (D-O) — e.g. two `name=` clauses;
  - **arg predicate on a wildcard tool** (decision #5) — `mcp__s__*(x=1)`.

## ALGORITHM (parse_matcher)
```
strip text; split off "(...)" arg-clause if present (error if unbalanced/multiple "(")
parse "mcp__server__tool" -> (server, tool); error if shape wrong
if arg-clause: error if >1 predicate; error if tool == WILDCARD
  parse name=value; if value is "{a,b,..}" -> value-set -> one Matcher per member
                    (each ArgPredicate(name,val,is_glob=False)); "v*" -> is_glob=True
  else single Matcher with ArgPredicate
else single Matcher(server, tool, arg=None)
return (matchers, [])
```
```
specificity: arg_rank = 1 if m.arg else 0
             concrete_tool   = 0 if m.tool==WILDCARD else 1
             concrete_server = 0 if m.server==WILDCARD else 1
matches: split canonical_tool "mcp__server__tool"; return
         (m.server in (WILDCARD, server)) and (m.tool in (WILDCARD, tool))
```

## DATA
- `parse_matcher` -> `(list[Matcher], list[str])`. Success: `(>=1 matchers, [])`.
  Failure: `([], [reason, ...])`.
- `specificity` -> `Specificity` NamedTuple.
- `matches` -> `bool`.

## TESTS (write first — `test_permissions_matcher.py`)
- Parse concrete `mcp__git__commit` -> one Matcher (`server="git"`, `tool="commit"`,
  `arg=None`), no errors.
- Parse wildcards: `mcp__git__*` (tool wildcard), `mcp__*__*` (both).
- Value-set expansion: `mcp__git__commit(msg={a,b})` -> **two** Matchers, each with an
  exact `ArgPredicate`; both `specificity().arg_rank == 1`.
- Glob arg: `mcp__git__push(remote=orig*)` -> one Matcher, `arg.is_glob is True`.
- Error rows (each -> `matchers == []`, non-empty errors):
  two predicates `...(a=1,b=2)`; arg-on-wildcard `mcp__git__*(x=1)`; malformed
  `not_a_tool`.
- `specificity` ranking (parametrized): arg-scoped `(1,1,1)` > exact-tool `(0,1,1)` >
  server-wildcard `(0,0,1)` > global `(0,0,0)`; assert lexicographic `>`.
- `matches` (parametrized): `mcp__git__*` matches `mcp__git__commit` but not
  `mcp__fs__read`; `mcp__*__*` matches anything; exact matches only itself.

## CHECKS
Same four checks as Step 1 (pylint, pytest with marker exclusions, mypy strict,
lint-imports). The leaf contract must still pass.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Following TDD, first
> write `tests/icoder/test_permissions_matcher.py` covering every case in TESTS
> (parametrize the specificity and matches tables), then implement
> `src/mcp_coder/icoder/permissions/matcher.py` per WHAT/HOW/ALGORITHM. Keep it pure:
> return errors as data, never log. Import only from `.model`. Use MCP tools only. Run
> pylint, pytest (unit-test marker exclusions), mypy(strict), and lint-imports; fix
> until green. Commit as one change.
