# Decisions — #1046 plan

Decisions taken in discussion with Marcus and applied to `pr_info/steps/`.

## 1. Persist round-trip tests assert the `Decision.source`, not only the policy

`resolver.py:191` returns `Decision(Policy.ALWAYS, Default(), None, None)` whenever no rule
matches, so every `_reload`-routed row asserting only `policy is Policy.ALWAYS` passed identically
when `write_rule` wrote nothing. `_reload` already returns a `Decision`, so callers now also assert
`source == Layer("local")`.

Applied to `step_4.md`: the `_reload` prose, `test_creates_file_and_directory_when_absent`, and
both params of `test_default_mode_value_is_not_mistaken_for_the_key`.

## 2. `test_session_grant_is_honoured_by_resolve` drives a real gateway

The hand-built `PermissionConfig` from the `add_runtime_rule` spy never exercised
`gateway.add_runtime_rule` — the store #1045 owns, which rebinds the frozen config. The test now
seeds a real `LangchainEnforcementGateway`, passes it as `AppCore(..., permission_gateway=...)`,
drives choice `2` and reads the grant back out of the gateway's own config. Precedent:
`tests/icoder/test_approval_wiring.py:384`.

Applied to `step_3.md`.

## 3. The `_insert_section` trailing comma is pinned by a test, not by more prose

The `comma = "" if the root object body holds no code characters else ","` rule never said where
the root body ends; on the `"{\n}\n"` new-file skeleton a literal reading emits a trailing comma.
Both scaffold tests parsed through `_strip_jsonc`, which strips trailing commas, so neither caught
it. Rather than re-specify the rule, `test_creates_file_and_directory_when_absent` now asserts the
produced text parses with plain `json.loads`.

Applied to `step_4.md`.

## 4. `_persist_target` reuses `_project_dir` instead of recomputing it

`ICoderApp.__init__` (`app.py:82-86`) already computes `self._project_dir` from
`runtime_info.project_dir` with a `Path.cwd()` fallback, and is the only subclass of
`StreamViewApp`. `StreamViewApp` gains a `_project_dir: Path` class annotation next to the existing
`_core: AppCore`, and `_persist_target` returns `self._project_dir / LOCAL_SETTINGS_RELPATH` — the
same "two implementations that can drift" objection that justifies moving `action_cancel_stream`.

Applied to `step_3.md` and `step_5.md`.

## 5. `step_4.md`'s pseudo-code is replaced by an invariants list

Plan review round 1 (`pr_info/plan_review_log_1.md`) ran five rounds and hit the round limit
without converging. Every "high" finding was an edge case inside `step_4.md`/`step_5.md`
pseudo-code, not a planning defect: prose pseudo-code is reviewable but not runnable, so review has
no termination condition. The plan was ~1333 lines of markdown for ~380 lines of production code.

The pseudo-code bodies of `_scan`, `_find_section_array`, `_insert_item`, `_insert_section`,
`_locate_item` and `write_rule`, plus their guard-justification paragraphs, are replaced by six
invariants. **Every guard rounds 1–5 added survives as a stated requirement** — the prose
implementation was cut, not the requirements. Kept: WHERE, WHAT (signatures), the `.importlinter`
note, the `_read` / `_atomic_write` DATA bullets, the whole test table and the `_reload` helper.
The tests are the specification.

`step_5.md`'s three-paragraph `except OSError` justification is reduced to one sentence.

Applied to `step_4.md` and `step_5.md`.

## 6. #1154 is rescoped to what step 1 delivers, and this PR closes it

Marcus decided the narrow `personal_bit` is #1154's **final** semantic, not a stopgap. #1154 is
retitled and its body amended in parallel: its sort key becomes the actual one
`(specificity, never_bit, personal_bit, policy.rank, layer, -index)`; its AC1 becomes the narrow
property (at equal specificity a `local`/`runtime` rule beats a `user`/`project` rule regardless of
`allow`/`ask`), plus a new AC pinning that a `user` `ask` still beats a `project` `allow` at equal
specificity. The `user` ↔ `project` direction is a recorded **won't-fix**: at equal specificity a
repo-committed `"allow"` must not silently override the user's global `"ask"`, which the originally
specified full `_LAYER_ORDER` hoist would have done — a security regression.

Consequence: step 1 satisfies #1154 in full and its commit carries `Closes #1154.`

Applied to `summary.md` (the "only partially addressed" paragraph collapsed to the rationale) and
`step_1.md` (header note, "Deliberately narrow" section, commit message, LLM prompt).

## 7. #1046's full-args AC is reworded to a containment property

The AC demanded the args widget's text *equal* `_format_args(args)` **and** carry no truncation —
impossible, since `_format_args` truncates single-line values over 120 chars via
`_render_value_full`. It is amended to: the args widget's text **contains every argument value
verbatim, with no truncation or ellipsis**.

No design change — the plan already gives the modal its own verbatim `format_args_full` instead of
reusing `detail_modal._format_args`. The plan nowhere quoted the old wording; the new wording is
now stated so the step-5 self-check cannot trip over it.

Applied to `step_2.md` (HOW section and LLM prompt) and `step_5.md` (LLM prompt self-check).

## Explicitly out of scope

- Modal tests stay in `tests/icoder/test_app_pilot.py`.
