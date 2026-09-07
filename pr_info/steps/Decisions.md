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

## 6. #1154 is rescoped to what step 1 delivers, and this PR closes it — SUPERSEDED by 12

> **Superseded.** Marcus reversed this later in the same review run; see decision 12. Kept for the
> history. Nothing below is in force any more except the `personal_bit` rationale, which decision
> 12 keeps.

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

## 8. Step 1's prose-site list covers all five `resolver.py` sites

Round 2 found the list incomplete: it named three resolver sites, but `resolver.py:142`
(`_resolve_config`'s docstring, "the ordinary 4-key contest") and `resolver.py:180` (the R14 bound
comment, "falls through to the ordinary 4-key contest") also describe a key that no longer exists.
Both verified against the file. The list is now five resolver sites plus the test module docstring,
with the two new ones as explicit items. #1154's own "Consequential edits" list already names
`_resolve_config`'s docstring, so this also keeps step 1 aligned with that issue.

Applied to `step_1.md` (WHERE row, HOW list, Acceptance, LLM prompt) and `summary.md`'s
"Files modified" row.

## 9. `test_no_temp_file_is_left_behind` is made falsifiable

The row asserted `.icoder/` holds no `*.tmp` file, but the implementation the same step specifies
(`tempfile.mkstemp(dir=target.parent)`) uses the default **empty suffix** and a `tmp` *prefix*, so
that glob can never match and the row passed whether or not a temp file leaked. It now asserts the
directory holds exactly one entry, `settings.local.json`.

Applied to `step_4.md`.

## 10. The summary's precedence heading names the personal bit, not the layer order

The heading read "Resolver precedence: layer moves above policy rank", which asserts exactly what
`step_1.md` forbids stating and what `summary.md` contradicts three lines below ("Two bits are
hoisted above `Policy.rank`; `_LAYER_ORDER` itself stays where it is"). Retitled to
"personal-layer bit moves above policy rank". The surrounding paragraph was checked and is correct
as written — it describes the pre-change key, not a hoisted layer order.

Applied to `summary.md`.

## 11. The resolver test counts are reconciled to `step_1.md`'s TDD section

`summary.md` said "Six new precedence cases; docstring notes on three existing tests" while
`step_1.md`'s TDD table names **seven** tests and its notes section says "**Two** existing tests …
add a docstring note to each", explicitly excluding
`test_no_runtime_rules_leaves_authored_precedence_unchanged`. Counted directly rather than trusted:
seven table rows, two notes.

The mismatch ran both ways — `step_1.md`'s own WHERE row also said "three existing tests",
contradicting its TDD section and its LLM prompt ("the two docstring notes"). The TDD section is
authoritative because it names each test individually. Both outliers corrected to seven / two.

Applied to `summary.md`'s "Files modified" row and `step_1.md`'s WHERE row.

## 12. The #1154 rescope is reverted: the issue stays open, this PR only partly addresses it

Marcus reversed decision 6. #1154 keeps its original text — the wider `_LAYER_ORDER` hoist
proposal — and stays **open**; the narrow-fix reasoning goes onto it as a comment instead of
replacing its body. The rescope would have settled a design question that is Marcus's to make:
whether a `user` `ask` should keep beating a `project` `allow` at equal specificity, and whether
layer order should outrank policy rank in general. #1046 needs neither answered.

Step 1's code is unchanged — still
`(specificity, never_bit, personal_bit, policy.rank, layer, -index)`, and the `personal_bit`
rationale from decision 6 still explains why that key was chosen. Only the issue-tracking framing
changes: no closing keyword for #1154 anywhere in step 1's commit body or LLM prompt, and #1154's
AC1 is explicitly recorded as unmet.

Applied to `step_1.md` (title, header note, "Deliberately narrow" wording, prose-site aside, commit
block, LLM prompt) and `summary.md` (opening dependency sentence, the paragraph below it, and the
steps-table row title).

## Explicitly out of scope

- Modal tests stay in `tests/icoder/test_app_pilot.py`.
