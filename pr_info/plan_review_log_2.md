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
