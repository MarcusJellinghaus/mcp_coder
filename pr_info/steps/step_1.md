# Step 1 — Model: `Rule.ref`, `Rule.matcher` widening, `origin` equality, skip guards

Read [summary.md](./summary.md) §4 (provenance) and §10 (accepted edge) first.

Pure typing/model step. No expansion logic yet — this makes the model able to *carry* provenance and
makes src tolerant of a matcher-less origin rule, so later steps stay small.

## WHERE

- `src/mcp_coder/icoder/permissions/model.py` (modify)
- `src/mcp_coder/icoder/permissions/resolver.py` (modify — 3 guards)
- `src/mcp_coder/icoder/permissions/gateway.py` (modify — 1 guard)
- `tests/icoder/test_permissions_model.py` (modify)
- `tests/icoder/test_permissions_optional_matcher.py` (create)

## WHAT

```python
# model.py
@dataclass(frozen=True)
class Rule:
    matcher: "Matcher | None"          # D15: widened, STILL REQUIRED (no default)
    policy: Policy
    layer: str
    source_path: Path | None = None
    ref: str | None = None             # D8: the literal authored token, e.g. "@github-write"


@dataclass(frozen=True)
class Matcher:
    server: str
    tool: str
    arg: ArgPredicate | None = None
    origin: Rule | None = field(default=None, compare=False)   # D14
```

Docstring updates: `Rule.matcher` is `None` **only** for a synthesised origin rule, which never
enters `config.rules` (D13); `Rule.ref` is non-`None` only on such a rule; `origin` is excluded from
equality and hash so provenance never changes matcher identity.

## HOW

- `ref` goes **last** with a default, so the three positional `Rule(...)` constructions
  (`loader.py:321`, `ui/stream_view.py:70`,
  `tests/llm/providers/langchain/test_approval_integration.py:174`) are unaffected.
- `field` is already imported in `model.py`.
- No `__hash__` work: a frozen dataclass derives `__eq__` **and** `__hash__` from `compare=True`
  fields only, so `compare=False` covers both. Assert it rather than assume it.

### The 4 guards (skip, never assert)

| Site | Guard |
|---|---|
| `resolver.py:63` (`_rule_sort_key` → `specificity(rule.matcher)`) | narrow before use; unreachable given the `:177` filter, but mypy needs it |
| `resolver.py:177` (`_resolve_config` candidate comprehension) | **mandatory**: add `rule.matcher is not None and` before `matches(...)` — this is the real filter that keeps a matcher-less rule out of the contest, and the only thing that enforces D13 in the resolver |
| `resolver.py:206` (`matched = best.matcher.origin or best`) | guard the `.origin` dereference: a matcher-less winner has no provenance to follow, so read `origin` only when `best.matcher is not None` and otherwise report `best` itself |
| `gateway.py:161` (`filter_tools`) | `rule.matcher is not None and rule.matcher.arg is not None` — a matcher-less origin rule means the tool is **hidden** (fail-closed, §10) |

Add a short comment at `:177` and `:161` naming D13: unreachable by construction, fail closed rather
than crash a live session.

## ALGORITHM

None — declarative model change plus four one-line narrowings.

## DATA

- `Rule.ref: str | None` — default `None`.
- `Rule.matcher: Matcher | None` — required positional; `None` only for an origin rule.
- `Matcher.origin` — unchanged type, now `compare=False`.

## Tests (write first)

`tests/icoder/test_permissions_model.py`:

1. Two matchers identical but for `origin` **compare equal** and **hash equal** (AC: "`Matcher`
   equality is unaffected by `origin`"). Build the differing origin as
   `Rule(None, Policy.ALWAYS, "project", ref="@git")`.
2. `Rule.ref` defaults to `None` and round-trips the authored token.
3. A `Rule` is constructible with `matcher=None` and keeps `policy`/`layer`/`source_path`/`ref`.

`tests/icoder/test_permissions_optional_matcher.py` (new — one focused file for the D15 fallout, so
neither the 731-line resolver test file nor the model test file grows off-topic):

4. `resolve()` on a config whose `rules` contains a matcher-less rule **plus** a normal matching rule
   returns the normal rule's policy — the matcher-less rule is skipped, nothing raises.
5. `resolve()` on a config whose only rule is matcher-less falls through to the default policy.
6. `gateway.filter_tools` hides a tool whose winning `NEVER` decision carries a matcher-less
   `matched_rule` (the §10 fail-closed edge), and still keeps an ordinary arg-scoped `NEVER` visible.

## LLM prompt

> Implement **step 1** of `pr_info/steps/summary.md` as described in `pr_info/steps/step_1.md`.
> Read the summary first (especially §4 and §10) for the settled decisions D8/D13/D14/D15.
>
> Test-driven: write the six tests listed under "Tests" first and watch them fail, then make the
> model change and add the four skip guards.
>
> Do not add expansion logic, do not touch `loader.py`/`skill_frame.py`, and do not give
> `Rule.matcher` a default value — D15 settled that it stays required. The guards must **skip** the
> rule, never assert or raise.
>
> Then run the checks listed at the end of the summary and fix anything they report. One commit.
