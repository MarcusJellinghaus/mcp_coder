# Step 5 — `skill_frame`: `@ref` lookup and `use:` block substitution

Read [summary.md](./summary.md) §5 first.

Flips the two remaining seams: `_classify` (drops `@ref` with a warning) and `build_frame` (blocks a
bare `use:`). No expansion happens here — `PermissionConfig.groups`/`.scenarios` are already
transitively expanded and ref-free, so a skill `@ref` is a **dict lookup**.

## WHERE

- `src/mcp_coder/icoder/permissions/skill_frame.py` (modify)
- `tests/icoder/test_permissions_skill_frame.py` (modify)

## WHAT

```python
def build_frame(
    tools_block: SkillToolsBlock | None,
    allowed_tools: Sequence[str] | None,
    *,
    enforce_skill_tools: bool,
    groups: Mapping[str, tuple[Matcher, ...]] | None = None,
    scenarios: Mapping[str, ScenarioBlock] | None = None,
) -> SkillFrame:

def _classify(
    token: str,
    *,
    side: str,
    groups: Mapping[str, tuple[Matcher, ...]],
) -> tuple[list[Matcher], str | None, str | None]:

def _classify_all(
    tokens: Sequence[str],
    *,
    side: str,
    groups: Mapping[str, tuple[Matcher, ...]],
) -> tuple[list[Matcher], list[str], tuple[str, ...]]:
```

## HOW

- The two new parameters are **keyword-only with a `None` default**, so all 24 existing `build_frame`
  call sites and tests compile unchanged. Use `None`, not `{}` — pylint flags mutable defaults;
  normalise once at the top of `build_frame` (`groups = groups or {}`).
- Their types are exactly `PermissionConfig.groups` and `PermissionConfig.scenarios`, so step 6's call
  site passes `config.groups` / `config.scenarios` verbatim with no conversion.
- Import `is_ref` / `ref_name` from `expand.py` and replace the local `token.startswith("@")` check.
  Do **not** import `expand` — nothing here needs a second expansion pass.
- Failure handling reuses I2.4's existing ladder (D10), **not** a global degrade: an unknown `@ref` is
  a `dropped` token, so the caller's existing machinery forces `base: none` on the deny side and
  `two_empties` blocks only if `allow` empties. One skill's typo must not force the whole session to
  `ask`.
- A **resolved** `@ref` emits no warning.
- `use:` + inline keys is already rejected upstream (`skill_tools.py:97-101` sets `errors`, and the
  `tools_block.errors` branch at `skill_frame.py:194-199` runs **before** the `use` branch). Keep that
  ordering — the AC is a regression assertion, not new work.
- An unknown `use: <name>` keeps today's outright block (there is no side to drop a missing whole
  block from); only the reason string changes from `"unsupported until I4.1"` to naming the unknown
  scenario. Note in the docstring that this is deliberate, per D10.
- A scenario's `base` is used verbatim — it is the security-relevant half of `use:`. Do not pass it
  through `as_base`; the loader already narrowed it to a `Base` literal.
- Update the class/module docstrings that say `@ref` is unsupported until I4.1.

## ALGORITHM

```
_classify(token, side, groups):
    if is_ref(token):
        members = groups.get(ref_name(token))
        if members:  return list(members), None, None            # resolved, no warning
        return [], f"unknown group reference {token!r} (ignored)", token   # D10 ladder
    ...unchanged: non-mcp__ ignored, parse_matcher, arg-predicate warning...

build_frame(...):
    ...unchanged: no declaration, legacy allowed_tools path (pass groups through)...
    if tools_block.errors:  return blocked            # unchanged — covers use: + inline keys
    if tools_block.use is not None:
        block = scenarios.get(tools_block.use)
        if block is None:
            return SkillFrame(PermissionFrame("none"), (), f"declares use: {…!r}, unknown scenario")
        return SkillFrame(PermissionFrame(block.base, block.allow, block.deny))
    ...unchanged: classify allow/deny, deny-dropped forces base=none, two_empties...
```

## DATA

- `SkillFrame.frame` for a resolved `use:` — a `PermissionFrame` carrying the scenario's whole
  `base` + `allow` + `deny`, `blocked_reason=None`, `warnings=()`.
- A resolved `@ref` contributes the group's member matchers into the side's matcher list; the members'
  `origin` is irrelevant here (`_resolve_frame` reports `matched_rule=None`).

## Tests (write first)

`tests/icoder/test_permissions_skill_frame.py`:

1. `@git` in a skill's `allow` with `groups={"git": (Matcher("git","log"),)}` → the member appears in
   `frame.allow`, **no warning**, not blocked.
2. `@git` in a skill's `deny` resolves into `frame.deny`, `base` **not** forced to `none`.
3. Unknown `@nope` in `allow` → dropped with a warning naming it, no global degrade, skill still runs
   when another `allow` token survived.
4. Unknown `@nope` in `deny` → `base` forced to `none` plus the existing narrowing warning (I2.4's D3).
5. Unknown `@nope` as the **only** `allow` token under `base: none` → blocked via `two_empties`, with
   the plain empty-allow reason.
6. `use: review` with a known scenario → `frame` is that whole block including `base`, not blocked.
7. `use: review` with `base: "none"` in the scenario → the frame's base is `"none"` (the
   security-relevant half actually lands).
8. Unknown `use: nope` → blocked, reason names the unknown scenario (and no longer says "I4.1").
9. **Regression (D5)**: `use:` + inline `allow` keys → blocked via `tools_block.errors`, reason
   mentions "cannot combine".
10. Omitting `groups`/`scenarios` entirely leaves every pre-existing behaviour unchanged (a `@ref`
    then reads as unknown → ladder, fail-closed).

## LLM prompt

> Implement **step 5** of `pr_info/steps/summary.md` as described in `pr_info/steps/step_5.md`.
> Read the summary first (§5) for D5 and D10.
>
> Test-driven: add the ten cases listed to `tests/icoder/test_permissions_skill_frame.py`, watch them
> fail, then change `skill_frame.py`.
>
> Key constraints:
> - `groups`/`scenarios` are keyword-only with a `None` default so the 24 existing call sites stay
>   untouched. Normalise `None` to `{}` inside the function; do not use a mutable default.
> - A skill `@ref` is a **lookup** into the already-expanded `config.groups` — do not import or call
>   `expand` here.
> - An unknown `@ref` uses I2.4's existing ladder (drop + warn on allow, force `base: none` on deny,
>   block only via `two_empties`). It must **not** set any global degrade.
> - An unknown `use: <name>` stays an outright block; change only the reason string.
> - Leave the `tools_block.errors` branch ahead of the `use` branch so D5's `use:` + inline-keys
>   rejection keeps working — that case is a regression assertion only.
>
> Then run the checks listed at the end of the summary. One commit.
