# Step 5 — Resolver: `runtime` becomes its own stage (R14) + degraded docstring (R15)

**Depends on:** nothing (independent of Steps 1–4; may run in parallel).

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

The existing 4-key sort lambda is lifted to a module-level `_rule_sort_key(ir)` so the partition
can reuse it; the `max(...)` call itself is unchanged apart from taking the named key.

```python
def _resolve_config(tool_name: str, config: PermissionConfig) -> Decision:
    # unchanged: degraded short-circuit, candidate collection
    runtime = [ir for ir in cands if ir[1].layer == "runtime"]
    authored = [ir for ir in cands if ir[1].layer != "runtime"]
    # Key the bound on the WINNING authored rule, not on "any authored never".
    top_authored = max(authored, key=_rule_sort_key) if authored else None
    blocked = top_authored is not None and top_authored[1].policy is Policy.NEVER
    if runtime and not blocked:          # runtime wins as a GROUP, before specificity ...
        cands = runtime                  # ... unless an authored `never` actually wins
    # unchanged: max(cands, key=_rule_sort_key), Decision construction
```

**2. `_resolve_frame` docstring — remove the now-false "degrade loosens" claim.**

The `base == "none"` + `config.degraded` branch returns `AFTER_APPROVAL` with a `Degraded` source
specifically so approval could rescue a sandboxed tool. Step 6 (R15) makes source-based denial
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
* **Bound the widening, and comment why.** R14 asks for a runtime `always` to
  beat an authored `ask`; an unbounded group short-circuit would also let a **broad** runtime
  `always` shadow a **specific** authored `never`, which is a security-relevant widening this
  issue does not need. With the guard an authored `never` falls through to the ordinary 4-key
  contest, so it loses only to a *strictly more specific* runtime rule, never to a broader one.
  The bound is close to free: `filter_tools` hides `never` tools from a turn-start snapshot, so a
  runtime grant cannot make such a tool callable in that turn anyway — without the bound the
  resolver would simply disagree with the tool list the model was given.
  Residual, recorded for #1048 (`/allow` quick commands, which carry no never-override confirm):
  a *specific* runtime grant still overrides a broader authored `never`.
* **The bound is keyed on the *winning* authored rule, not on "any matching authored `never`".**
  A rule set can hold both, and "any" then breaks R14's own headline case:

  ```
  project layer:  "never": ["mcp__s__*"]     (broad)
                  "ask":   ["mcp__s__t"]     (specific)
  runtime grant:  Rule(Matcher("s","t"), ALWAYS, "runtime")
  ```

  The broad `never` matches, so "any" skips the short-circuit; the specific authored `ask` then
  beats the runtime `always` on `Policy.rank` (`AFTER_APPROVAL` 1 > `ALWAYS` 0 at equal
  specificity), and the `scope=session` grant silently does nothing — the user is re-prompted
  every turn, contradicting the acceptance criterion this step exists for. Sorting the authored
  candidates first and testing only the **top** one costs one extra `max()` over a list the
  resolver already knows how to order.
* Do **not** touch `resolve()`, `_resolve_frame`'s logic, `matcher.py`, or `model.py`.

## ALGORITHM

```
KEY = (specificity, policy.rank, _LAYER_ORDER[layer], -index)   # lifted to _rule_sort_key

collect cands = [(index, rule) for matching rules]          # unchanged
runtime  = [c for c in cands if c.rule.layer == "runtime"]
authored = [c for c in cands if c.rule.layer != "runtime"]
top_authored = max(authored, key=KEY) if authored else None
if runtime and not (top_authored and top_authored.rule.policy is NEVER):
    cands = runtime                                          # top-priority stage, bounded
best = max(cands, key=KEY)                                   # unchanged
return Decision(best.policy, Layer(best.layer), matched, None)                    # unchanged
```

## DATA

No new types. `Decision.source` for a runtime win is `Layer("runtime")` — which Step 6 flattens to
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
4b. **The bound reads the winning authored rule, not any authored rule.** Project layer with
    **both** `"never": ["mcp__s__*"]` and `"ask": ["mcp__s__t"]`, plus runtime
    `Rule(Matcher("s","t"), ALWAYS, "runtime")` → resolves `ALWAYS` with `Layer("runtime")`.
    The specific `ask` outranks the broad `never` among the authored candidates, so the bound
    does not engage. An `any`-matching bound resolves `AFTER_APPROVAL` here and re-prompts on
    every turn; tests 1 and 3 both pass under that bug, so this case is the only one that catches
    it.
5. Runtime rules contest **among themselves** normally: two runtime rules of different
   specificity → the more specific wins.
6. No runtime rules present → behaviour is byte-identical to today.
7. **Regression:** existing
   `test_later_layer_wins_at_equal_specificity_and_policy` stays green (verify, do not edit).

## CHECKS

`run_pylint_check`, `run_pytest_check`, `run_mypy_check` — all green.

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` (§2.4 and §2.5) and `pr_info/steps/step_5.md`, then implement
> Step 5 only.
>
> In `src/mcp_coder/icoder/permissions/resolver.py`, make the `runtime` layer its own top-priority
> stage in `_resolve_config`: lift the existing 4-key sort lambda to a module-level
> `_rule_sort_key`, partition the matching candidates on `rule.layer == "runtime"`, and contest
> within the runtime group when it is non-empty **and the top-ranked authored (non-runtime)
> candidate is not `never`**, otherwise contest the rest. Leave `_LAYER_ORDER`,
> the sort keys themselves, and every other code path untouched. Add a comment explaining that
> layer is only the third sort key and `Policy.rank` ranks `AFTER_APPROVAL` above `ALWAYS`, which
> is why a session grant would otherwise lose to an authored `ask` — and a second comment
> explaining the bound: R14 only needs runtime to beat `ask`, and letting a broad runtime
> `always` shadow a specific authored `never` would be a security-relevant widening this issue
> does not need (an authored `never` then loses only to a strictly more specific runtime rule).
>
> Key the bound on the **winning** authored rule, not on "any matching authored `never`". A config
> holding a broad `"never": ["mcp__s__*"]` **and** a specific `"ask": ["mcp__s__t"]` would
> otherwise skip the short-circuit, the `ask` would beat the runtime `always` on `Policy.rank`,
> and the `scope=session` grant would silently never take effect. Test case 4b covers exactly
> that shape.
>
> Also correct the `_resolve_frame` docstring's "the one place degrade loosens" claim and the
> module docstring's precedence sentence — Step 6 (R15) makes degraded configs deny outright, so
> that branch is no longer a loosening.
>
> Write the eight test cases listed in the step first; confirm case 1 fails before the change and
> that the existing `test_later_layer_wins_at_equal_specificity_and_policy` stays green.
>
> Use MCP tools only. Finish with `run_pylint_check`, `run_pytest_check`, `run_mypy_check` all
> green, then one commit.

---

## Implementation note (written after the fact)

**Shape:** implemented exactly as planned — `_rule_sort_key` lifted to module level, the
partition + winning-authored-`never` bound in `_resolve_config`, and the two docstring
corrections. No deviations, no extra patch sites, nothing outside
`src/mcp_coder/icoder/permissions/resolver.py` and
`tests/icoder/test_permissions_resolver.py`.

Two docstrings beyond the two named in WHERE were touched, both for the same reason (they
described the old flat precedence): the `_resolve_config` docstring gained a paragraph naming the
runtime stage and its bound, and the module docstring's precedence sentence now reads
`user->project->local` with `runtime` described as a stage above it.

**TDD result (tests written first, run before the change):** cases 1, 2 and 4b were red, each
resolving `AFTER_APPROVAL`/`Layer("project")` instead of `ALWAYS`/`Layer("runtime")` — exactly the
R14 symptom. Cases 3, 4 and 5 (the two bound directions, the documented residual, and the
intra-runtime contest) were already green before the change, as the step anticipated; they are
regression guards, not drivers. Case 7's
`test_later_layer_wins_at_equal_specificity_and_policy` stays green unedited: its four rules are
all `ALWAYS`, so the runtime group short-circuit selects the single runtime rule the 4-key sort
was already selecting.

**Checks:** `run_pylint_check` and `run_mypy_check` clean on both the permissions package and the
test file; `run_format_code` reports no changes.

**Local environment caveats (all pre-existing, none caused by this step):**

1. The stale installed `mcp_workspace` still breaks pytest collection repo-wide (Steps 1–4
   recorded the same); every run below used
   `PYTHONPATH=C:\Users\Marcus\Documents\GitHub\mcp-workspace\src`.
2. The whole-repo run **and** the whole-`tests/icoder` run both exceed the tool's 300s timeout on
   this machine, so pytest verification was done as targeted per-file runs: the ten
   permission/wiring/service files (248 passed) plus `test_icoder_permission_wiring.py`
   (6 passed, 2 skipped) plus `test_app_core.py` / `test_skills.py` / `test_replay.py` /
   `test_cli_icoder.py` (107 passed). The change is a pure function in
   `permissions/resolver.py`, so the untried remainder is the textual UI suite, which does not
   reach the resolver.
