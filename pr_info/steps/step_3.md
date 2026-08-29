# Step 3 — Resolver: `runtime` becomes its own stage (R14) + degraded docstring (R15)

**Depends on:** nothing (independent of Steps 1–2; may run in parallel).

Without this, the `scope=session` acceptance criterion is **unsatisfiable** for its canonical case:
a session grant loses to an authored `ask` at equal specificity, which is the single most common
way a tool becomes gated in the first place.

---

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/icoder/permissions/resolver.py` | **modify** — `_resolve_config`, `_resolve_frame` docstring, module docstring |
| `tests/icoder/test_permissions_resolver.py` | **modify** — add R14 cases |

## WHAT

Two changes, both small.

**1. `_resolve_config` — partition candidates before the specificity contest.**

```python
def _resolve_config(tool_name: str, config: PermissionConfig) -> Decision:
    # unchanged: degraded short-circuit, candidate collection
    runtime = [ir for ir in cands if ir[1].layer == "runtime"]
    authored_never = any(
        ir[1].layer != "runtime" and ir[1].policy is Policy.NEVER for ir in cands
    )
    if runtime and not authored_never:   # runtime wins as a GROUP, before specificity ...
        cands = runtime                  # ... but never as a shortcut past an authored `never`
    # unchanged: max(...) over the existing 4-key sort, Decision construction
```

**2. `_resolve_frame` docstring — remove the now-false "degrade loosens" claim.**

The `base == "none"` + `config.degraded` branch returns `AFTER_APPROVAL` with a `Degraded` source
specifically so approval could rescue a sandboxed tool. Step 4 (R15) makes source-based denial
collapse that to an effective `NEVER`. The behaviour is unchanged from M2, so nothing breaks — but
the docstring stops describing unreachable intent. Update the module docstring's precedence
sentence in the same edit (`user->project->local->runtime` is no longer a flat ordering).

## HOW

* Keep `_LAYER_ORDER` exactly as it is — it still orders `user`/`project`/`local` **within** the
  non-runtime group, and orders runtime rules among themselves (a no-op today, but I4.2/#1048
  writes several runtime rules that must resolve against each other normally).
* Explain **why** in a comment: `_LAYER_ORDER` is only the *third* sort key and
  `Policy.rank` puts `AFTER_APPROVAL` (1) above `ALWAYS` (0), so without the partition a runtime
  `ALWAYS` loses to an authored `ask` on the same matcher.
* **Bound the widening (`authored_never`), and comment why.** R14 asks for a runtime `always` to
  beat an authored `ask`; an unbounded group short-circuit would also let a **broad** runtime
  `always` shadow a **specific** authored `never`, which is a security-relevant widening this
  issue does not need. With the guard an authored `never` falls through to the ordinary 4-key
  contest, so it loses only to a *strictly more specific* runtime rule, never to a broader one.
  The bound is close to free: `filter_tools` hides `never` tools from a turn-start snapshot, so a
  runtime grant cannot make such a tool callable in that turn anyway — without the bound the
  resolver would simply disagree with the tool list the model was given.
  Residual, recorded for #1048 (`/allow` quick commands, which carry no never-override confirm):
  a *specific* runtime grant still overrides a broader authored `never`.
* Do **not** touch `resolve()`, `_resolve_frame`'s logic, `matcher.py`, or `model.py`.

## ALGORITHM

```
collect cands = [(index, rule) for matching rules]          # unchanged
runtime = [c for c in cands if c.rule.layer == "runtime"]
authored_never = any(c.rule.layer != "runtime" and c.rule.policy is NEVER for c in cands)
if runtime and not authored_never: cands = runtime           # top-priority stage, bounded
best = max(cands, key=(specificity, policy.rank, _LAYER_ORDER[layer], -index))   # unchanged
return Decision(best.policy, Layer(best.layer), matched, None)                    # unchanged
```

## DATA

No new types. `Decision.source` for a runtime win is `Layer("runtime")` — which Step 4 flattens to
the plain string `"runtime"` for the `approval_request` payload.

## TESTS (write first)

1. **Canonical R14 case:** project layer `"ask": ["mcp__s__t"]` + runtime
   `Rule(Matcher("s","t"), Policy.ALWAYS, "runtime")` → resolves `ALWAYS` with `Layer("runtime")`.
   (Assert this fails before the change — it currently resolves `AFTER_APPROVAL`.)
2. A runtime rule wins even when a **more specific** authored `ask`/`allow` rule exists (the
   group is consulted before the specificity contest) — intended widening, per R14's note.
3. **Bound:** a *broad* runtime `always` (e.g. `Matcher("s", None)`) does **not** shadow a
   *specific* authored `never` (`"never": ["mcp__s__t"]`) → still `NEVER`.
4. **Bound, other side:** a runtime `always` on the same matcher as an authored `never` also
   loses (equal specificity, `Policy.rank` favours `NEVER`), while a *strictly more specific*
   runtime `always` against a broader authored `never` wins — the documented residual.
5. Runtime rules contest **among themselves** normally: two runtime rules of different
   specificity → the more specific wins.
6. No runtime rules present → behaviour is byte-identical to today.
7. **Regression:** existing
   `test_later_layer_wins_at_equal_specificity_and_policy` stays green (verify, do not edit).

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check` — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.4 and §2.5) and `pr_info/steps/step_3.md`, then implement
> Step 3 only.
>
> In `src/mcp_coder/icoder/permissions/resolver.py`, make the `runtime` layer its own top-priority
> stage in `_resolve_config`: partition the matching candidates on `rule.layer == "runtime"` and
> contest within that group when it is non-empty **and no authored (non-runtime) matching rule is
> `never`**, otherwise contest the rest. Leave `_LAYER_ORDER`,
> the 4-key sort, and every other code path untouched. Add a comment explaining that layer is only
> the third sort key and `Policy.rank` ranks `AFTER_APPROVAL` above `ALWAYS`, which is why a
> session grant would otherwise lose to an authored `ask` — and a second comment explaining the
> `authored_never` bound: R14 only needs runtime to beat `ask`, and letting a broad runtime
> `always` shadow a specific authored `never` would be a security-relevant widening this issue
> does not need (an authored `never` then loses only to a strictly more specific runtime rule).
>
> Also correct the `_resolve_frame` docstring's "the one place degrade loosens" claim and the
> module docstring's precedence sentence — Step 4 (R15) makes degraded configs deny outright, so
> that branch is no longer a loosening.
>
> Write the seven test cases listed in the step first; confirm case 1 fails before the change and
> that the existing `test_later_layer_wins_at_equal_specificity_and_policy` stays green.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` all
> green, then one commit.
