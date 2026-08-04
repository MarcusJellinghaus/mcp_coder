# Plan review log 2 — issue #1061 (I2.4)

Supervised plan review run 2. Plan: `pr_info/steps/` (5 steps).
Branch up to date with `main`, CI passed. Run 1 (`plan_review_log_1.md`) completed 2 rounds.

## Round 1 — 2026-08-03
**Findings**:
`step_1.md:48` — critical — `raw = meta.get("tools"); if raw is None: return None` maps a present-but-null `tools:` to ABSENT (fail-open, `frame=None`) although the AC and mapping table list "present-but-null/empty" as malformed → BLOCKED.
`step_3.md:58` — medium — the frame map is built for every provider with a bare `ENFORCE_SKILL_TOOLS`; once #1062 flips it to `True`, legacy `Bash(...)`-only skills get a `blocked_reason` and are refused under the **claude** provider, where native `allowed-tools` handles them.
`step_4.md:49` — medium — rendering blocked commands as `Option(..., disabled=True)` makes them un-tab-completable with no feedback (`select_highlighted()` returns `None`; Textual's `validate_highlighted` does not skip disabled rows), so D9(1)'s "invoking prints the reason" surface becomes unreachable from the dropdown.
`step_2.md:17` — low — the prescribed "annotate the `base` local in `build_legacy_frame`" does not apply: there is no `base` local (inline ternary at `gateway.py:80`, resolved from the argument's type context).
`step_1.md:52` — low — the `use:`+inline error branch falls through to the shared return with `base`/`allow`/`deny`/`errors` unbound, and the `advisories` comprehension calls `.startswith` over `allow+deny` even after the `list[str]` check failed.
`step_2.md:85` — low — `two_empties` receives the D3-forced `base="none"`, so a dropped `deny` entry plus an all-dropped `allow` escalates D3's "run + warn" into a D8 block with a misleading reason.
`step_4.md:57` — low — the refusal guard returns before `registry.dispatch`, so a blocked command logs `input_received` + `output_emitted` but never `command_matched`.
`step_5.md:46` — low — placing the notices "after the existing dim runtime banner" nests them inside `on_mount`'s `elif self._core.runtime_info:` branch, silently dropping the degraded-config line when `runtime_info` is `None`.
`step_5.md:15` — low — a new `tests/icoder/test_runtime_banner.py` splits `runtime_banner.py` coverage from the existing `tests/icoder/test_banner.py`.

Run-1 fixes verified as correctly applied (all six): `as_base` narrowing, `permission_degraded` scope hoist, `permission_warning` event-log routing, `forbidden_modules` extension (verified no leaf module imports `icoder.core`/`icoder.skills`), the D14 both-blocks test, and the frame-no-leak test. All 18 acceptance criteria and D1–D15 map to a step and an enumerated test.

**Decisions**:
All nine accepted. Two raised as design questions were resolved by the user: `step_4.md:49` — keep the autocomplete `Option` **enabled** (mark the label only), since the AC requires only *marking* and D7/D9(1) require that invoking a blocked command prints its reason. `step_2.md:85` — option C: keep the D8 predicate on the *forced* base (D7 wins: never burn a turn on a zero-tool skill), but return **two distinct** `blocked_reason` strings so a deny-caused block names the dropped `deny` entry rather than an empty `allow`.

**Changes**:
applied — `summary.md`, `step_1.md`, `step_2.md`, `step_3.md`, `step_4.md`, `step_5.md`, plus a new `pr_info/steps/Decisions.md` recording R2-1 … R2-9.

## Round 2 — 2026-08-03
**Findings**:
`step_2.md:55` — medium — `classify(...) -> (matchers, warning|None, dropped: bool)` cannot name the
dropped token, yet the very same step promises a deny-caused `blocked_reason` reading
`"... a deny entry could not be resolved (<token>) ..."` and a test asserting that text "names the
dropped `deny` entry". With a bool, `two_empties(..., deny_forced=...)` and the D3 warning can only
say *that* something was dropped, never *what* — R2-6's fix is unimplementable as specified.
`step_2.md:61` — low — the arg-scoped `#1053` warning text (`warn(arg-scoped elevates whole tool
until #1053)`) is shared by both sides even though `classify` already takes `side`; on the `deny`
side an arg predicate over-**denies**, so "elevates the whole tool" is factually inverted — the same
defect run 1 flagged for the old shared text, reintroduced by the single-string helper.
`step_2.md:75` — low — `blocked_reason="; ".join(errors)` references an unbound `errors`; in that
branch the list is `tools_block.errors` (the local `errors` belongs to `parse_tools_block` in
Step 1). A literal implementation NameErrors.
`step_3.md:65` + `Decisions.md:9` — low — both narrow the provider-agnostic reach to
"`tools_block.errors`-driven blocking", but a **well-formed** rich block also blocks
provider-agnostically: D8 (`base: none`, nothing survived parse) and bare `use:` (D7b) set
`blocked_reason` with `errors == ()`. `summary.md` already says "`tools_block`-driven"; the two
narrower phrasings invite an implementer to gate D8/D7b blocking behind `provider == "langchain"`.
`step_5.md:58` — low — `f"⚠ /{name} is disabled: …"` prints the **raw** key of the
`{skill_name: SkillFrame}` map, but the registered command is `"/" + skill.name.lower()`
(`src/mcp_coder/icoder/skills.py:194`). A mixed-case skill directory would be advertised at startup
under a command the user cannot type, and the line would disagree with the command Step 4's refusal
guard matches (`handle_input` lower-cases the leading token).
`step_1.md:9`, `step_2.md:12` + their LLM PROMPTs, `step_3.md:106`, `summary.md:90` — low — the new
test files were named `tests/icoder/test_skill_tools.py` / `test_skill_frame.py`, breaking the
`tests/icoder/test_permissions_<module>.py` convention every other `permissions/` module follows
(`test_permissions_matcher.py`, `test_permissions_resolver.py`, `test_permissions_gateway.py`, …).

**Decisions**:
All six accepted; no design questions raised. Findings 1–3 (`step_2.md`) and the WHERE-section half of
finding 6 were applied first; findings 4–6 were completed in this pass. Recorded as R2-10 … R2-15 in
`pr_info/steps/Decisions.md`. Rationale kept inline in the plan text for 4 and 5 so neither is
"simplified" back: the D8/`use:` blocking paths carry no `errors`, and the startup notice must print
the *registered* (lower-cased) command name.

**Changes**:
applied — `step_1.md` (test filename in WHERE + LLM PROMPT), `step_2.md` (dropped-token classifier,
`deny_dropped` tuple, side-selected `#1053` wording, `tools_block.errors` join, test filename),
`step_3.md` (`tools_block`-driven wording, `test_permissions_skill_frame.py` reference),
`step_5.md` (lower-cased skill name in `format_startup_permission_notices` + DATA/TESTS/LLM PROMPT),
`summary.md` (created-files list), `Decisions.md` (R2-2 wording + new R2-10 … R2-15).

**Status**: all six findings applied; plan consistent across `summary.md`, `Decisions.md` and
steps 1–5. No source files touched. Ready for implementation.

## Round 3 — 2026-08-03
**Findings**:
`summary.md:120` (+ the five LLM PROMPTs at `step_1.md:103`, `step_2.md:154`, `step_3.md:141`,
`step_4.md:105`, `step_5.md:102`) — medium — the per-step verification loop is pylint + pytest +
mypy + `lint-imports`, omitting **ruff**, yet the final AC requires "ruff-docstrings clean" and CI
runs `ruff check src tests` with `select = ["D","DOC"]` and `preview = true`. Every new public
function returns a value (`parse_tools_block`, `build_frame`, `as_base`, `two_empties`,
`format_startup_permission_notices`, `CommandRegistry.get`, `AppCore.broken_skills`), so a missing
`Returns:` section trips DOC201 and every step as written can land CI-red. (`lint-imports` is *not*
in CI — the plan being stricter there is intentional and stays.)
`step_5.md:46` — low — the HOW snippet calls `output.append_text(...)`, but `output` is bound only
inside `on_mount`'s `elif self._core.runtime_info:` branch (`ui/app.py:152`) and R2-8 deliberately
renders the notices *outside* that branch, so the literal implementation raises `UnboundLocalError`
in exactly the `runtime_info is None` case Step 5's own `test_app_pilot` assertion covers.
`step_3.md:39,41` — low — Step 3 deletes `build_legacy_frame` but never mentions the prose that
documents it: `gateway.py`'s module-docstring third paragraph and `RealLLMService.stream`'s docstring
(its `allowed_tools` `Args:` entry plus the `permission_warning`/`build_legacy_frame` paragraph and
`Yields:` note) would be left describing deleted code and a removed parameter. Neither ruff nor
pylint catches stale prose.

Re-verified against source this round: `skills.py:194`, `app_core.py`'s `replace(action, text=…)`
hop, `app.py:415`, `gateway.py`'s inline-ternary `base` (R2-4 holds), `parse_matcher`'s
all-or-nothing error contract (so Step 2's `dropped=token` classifier is sound),
`select_highlighted()` returning `None` on `disabled=True` options (R2-3 holds), and — new this
round — that **every** `PermissionFrame(base=…)` construction in `src/` and `tests/` uses a string
literal, so D15's `Base` retype is safe under CI's `mypy --strict src tests` with no `gateway.py`
or `resolver.py` change. Step 3's test-migration list is complete: every file in `tests/` matching
`allowed_tools`/`enforce_skill_tools`/`build_legacy_frame` is listed. All 18 acceptance criteria and
D1–D15 map to a step and an enumerated test; the 15 prior fixes are correctly and consistently
applied across `summary.md`, `Decisions.md` and steps 1–5.

**Decisions**:
All three accepted by the coordinator; no design questions, no user escalation. Recorded as
R2-16 … R2-18 in `pr_info/steps/Decisions.md`. `lint-imports` explicitly stays in the loop despite
being absent from CI. While rewriting Step 1's check clause, its tool prefix was corrected from
`mcp__tools-py__*` to `mcp__mcp-tools-py__*` (the other four steps name the checks in prose).

**Changes**:
applied — `summary.md` (ruff in the footer + why), `step_1.md` … `step_5.md` (ruff in each LLM
PROMPT), `step_3.md` (HOW: rewrite the gateway module docstring and `RealLLMService.stream`'s
docstring), `step_5.md` (HOW + LLM PROMPT: bind `output = self.query_one(OutputLog)` inside the
notices block), `Decisions.md` (R2-16 … R2-18).

**Status**: all three findings applied; consistency sweep over `pr_info/` confirms the
verification-loop wording, the `output.append_text` call site and the `build_legacy_frame` docstring
references now agree across `summary.md`, `Decisions.md` and steps 1–5. No source files touched.
Ready for implementation.

## Round 4 — 2026-08-03
**Findings**: None. A fourth independent engineer re-verified the plan end-to-end against issue #1061
(D1–D15, 18 ACs), the linked epic #1038 and design ref #1037, and the real source tree.

Re-verified as correct: all round-3 fixes (ruff in the summary footer and all five step prompts, the
`output = self.query_one(OutputLog)` binding in step 5's un-nested notices block, step 3's two stale
docstrings); no stale references survive from rounds 1–2 (`test_skill_tools.py`/`test_skill_frame.py`,
`deny_forced`, `dropped: bool`, `test_runtime_banner.py`, `tool_permissions` all absent). Plan claims
checked against source: `skills.py:194` lower-casing, `gateway.py:79` inline ternary, `app.py:150/415`,
the `config` local's scope, `select_highlighted()` on a disabled Option, `parse_matcher`'s signature,
`resolver._resolve_frame` (D11 — no resolver change needed), all 23 `PermissionFrame(base=…)` sites
being string literals (D15 safe under `mypy --strict src tests`), the `permissions_leaf_isolation`
extension, and step 3's seven-file test-migration list being exactly complete.

**Decisions**: No action. Loop terminates.
**Changes**: None.
**Status**: no changes needed

## Final Status

**Rounds run:** 4 (rounds 1–3 produced plan changes; round 4 produced none, closing the loop).
**Findings triaged:** 18 accepted and applied — 17 handled autonomously as mechanical plan fixes,
1 escalated to the user.

**User decision:** the conflict between D8's block predicate and D3's forced `base="none"` — a dropped
`deny` entry can force `base="none"` and thereby trip D8 on a skill the author wrote as `base: inherit`.
Options offered: (A) predicate reads the *declared* base, so D3's "runs on a narrowed frame + warning"
stands; (B) keep the forced base, block anything that ends up zero-tool; (C) block, but with a distinct
reason string naming the dropped `deny` entry as the real cause. **User chose C** — recorded as R2-6.

**Commits produced:**
| SHA | Scope |
|---|---|
| `e9e7f0b` | Round 1 — nine findings (R2-1…R2-9), incl. the critical present-but-null `tools:` fail-open fix |
| `14e21da` | Round 2 — six findings (R2-10…R2-15) |
| `c2491af` | Round 3 — three findings (R2-16…R2-18) |

**Most material fixes:** present-but-null `tools:` reclassified MALFORMED (closing a fail-open hole on
the issue's own primary risk boundary); `enforce_skill_tools` gated to the langchain provider so #1062's
flip cannot block legacy skills under the Claude provider; blocked autocomplete rows kept selectable so
D7's "invoking it prints the reason" is reachable; ruff added to every step gate (the new public
functions would otherwise have landed CI-red on DOC201).

**Verdict:** all 18 acceptance criteria and D1–D15 map to a step with an enumerated test; plan claims
verified line-for-line against the source; step sizing conforms to `planning_principles.md`; no scope
drift into I4.1 / I5.1 / I5.4 / #1062. **The plan is ready for approval.**
