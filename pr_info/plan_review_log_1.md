# review-plan review log 1

## Round 1 — 2026-11-24
**Findings**:
Reviewing plan against verify_sections source; a few more reads to go.Checking file sizes and the help/docs strings referenced by step 4.Verifying the `Row` signature used by step 5, then emitting findings.`pr_info/steps/step_3.md:23` — medium — Only the `(source, table)` pair is unpacked; the plan never checks that `prompts` is a table. Today `mcp-coder.toml` is never read, so `prompts = "x"` there is harmless. After this step it raises `AttributeError` on `.get`, reached through `load_prompts`, which `verify`, `llm/interface.py` and `icoder` call without error handling. That breaks Decision 2's "no new crash points". Treat a non-dict value as the default and log a warning; add a test for it.

`pr_info/steps/step_4.md:27` — medium — `project_dir / found[1]` has no type check. A non-string `labels-config` in `mcp-coder.toml` (e.g. `labels-config = 5`) raises `TypeError` in a path that used to ignore it. That is a new crash point against Decision 2. Return `None` and log a warning when the value is not a `str`; add a test for it.

`pr_info/steps/step_2.md:59` — low — The step adds an `indent` parameter to `_format_code_row`, but says the `ValueError` branch "stays the same", and that branch hard-codes indent 4. A non-bool `format_code` in a repo without `pyproject.toml` would then show its `[ERR]` row at indent 4 while the other rows use 2. The error row should use `indent` too.

`pr_info/steps/step_4.md:9` — low — `docs/cli-reference.md:614` also lists the labels-config resolution order as "`labels-config` in `pyproject.toml`". It mirrors the `gh_parsers.py` help text, but only `label-setup.md` is in the update list. Add `cli-reference.md` there.

`pr_info/steps/step_5.md:49` — low — The "cannot be parsed" warning goes only to the PROJECT section, yet a malformed file also resets `prompts` to defaults. The issue's constraint says prompts rows belong in PROMPTS. Also emit a PROMPTS-section warning for a malformed file, or state explicitly that this case stays PROJECT-only.
**Decisions**:
Verdict(decision='tasks', tasks=['pr_info/steps/step_3.md:23 — after unpacking (source, table), check that `prompts` is a dict. If it is not, fall back to the defaults and log a warning instead of calling `.get` on it, so `load_prompts` cannot raise AttributeError. Add a test with `prompts = "x"` in mcp-coder.toml.', 'pr_info/steps/step_4.md:27 — before `project_dir / found[1]`, check that the `labels-config` value is a `str`. If it is not, return None and log a warning. Add a test with `labels-config = 5` in mcp-coder.toml.', 'pr_info/steps/step_2.md:59 — change the `_format_code_row` ValueError branch to use the new `indent` parameter instead of the hard-coded indent 4. Update the step text to say so.', 'pr_info/steps/step_4.md:9 — add `docs/cli-reference.md` (~line 614, the labels-config resolution order) to the list of docs to update, matching the gh_parsers.py help text and label-setup.md.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-24
**Findings**:
Still reviewing the plan: I'm checking the helper signatures that step 5 relies on (`SectionBuilder.add`, `Row`, `unknown_key_hint`, and the PROMPTS section in `verify.py`).Checking `tach.toml` and `.importlinter` to confirm the planned imports from `config.toml_utils` are allowed.Checking whether any installed sibling package imports `mcp_coder.utils.toml_utils`, since step 1 moves it with no shim.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
