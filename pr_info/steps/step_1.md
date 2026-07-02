# Step 1: Add `network_proxy` label mapping + test coverage

**One commit.** See `pr_info/steps/summary.md` for full context and rationale.

This is a single logical change: the test edits and the source edit are
mutually dependent (the key-set test fails without the `_LABEL_MAP` entry, and
the entry is meaningless without the test). Following TDD, write/adjust the
tests first, watch them fail, then add the one-line source change to make them
pass.

## WHERE

- `tests/cli/commands/test_verify_format_section_basic.py`
  (class `TestGitHubLabelMappings`)
- `src/mcp_coder/cli/commands/verify.py` (module-level dict `_LABEL_MAP`)

## WHAT

No new functions or signatures. Data-only changes:

1. **Test — key set.** Add `"network_proxy"` to the `_GITHUB_KEYS` tuple in
   `TestGitHubLabelMappings`, placed after `"api_base_url"` to mirror the
   source order:
   ```python
   _GITHUB_KEYS = (
       "api_base_url",
       "network_proxy",
       "token_configured",
       ...
   )
   ```

2. **Test — docstring.** Make `test_all_github_keys_in_label_map`
   count-agnostic (it currently hardcodes a stale count):
   ```python
   def test_all_github_keys_in_label_map(self) -> None:
       """All GitHub check keys exist in _LABEL_MAP."""
   ```

3. **Test — rendering.** Extend the existing
   `test_format_section_renders_github_labels` (do NOT add a new method) with a
   `network_proxy` entry and two assertions:
   ```python
   result: dict[str, Any] = {
       "token_configured": {"ok": True, "value": "YES"},
       "repo_accessible": {"ok": True, "value": "owner/repo"},
       "network_proxy": {
           "ok": False,
           "value": "api=api.x.ghe.com:443 tcp=timeout proxy_env=HTTPS_PROXY pac=present",
       },
       "overall_ok": True,
   }
   output = _format_section("GITHUB", result, self._symbols())
   assert "Token configured" in output
   assert "Repo accessible" in output
   assert "Network / proxy" in output      # labeled row present
   assert "network_proxy" not in output    # raw key does not leak
   assert "[OK]" in output
   assert "[ERR]" in output          # failed probe renders [ERR] (ok=False), per issue rationale
   ```

4. **Source.** Add one entry to `_LABEL_MAP` in the GitHub section, immediately
   after `"api_base_url"`:
   ```python
   # GitHub section
   "api_base_url": "API base URL",
   "network_proxy": "Network / proxy",
   "token_configured": "Token configured",
   ...
   ```

## HOW (integration points)

- No imports, decorators, or wiring change. `_format_section` already looks up
  labels via `_LABEL_MAP.get(key, key)` and already iterates every non-`overall_ok`
  dict entry, so the new label is picked up automatically.
- `verify_github()` (called in `execute_verify`) already emits `network_proxy`;
  no change there.

## ALGORITHM

No new logic. Existing render path (unchanged), shown for reference:

```
for key, entry in result.items():
    if key == "overall_ok" or not isinstance(entry, dict): continue
    label  = _LABEL_MAP.get(key, key)   # now returns "Network / proxy"
    marker = [OK] if ok else [ERR] if ok is False else [WARN]  # ok drives marker
    emit_row(label, marker, str(entry["value"]))               # single line
```

## DATA

- `_LABEL_MAP`: `dict[str, str]` — gains key `"network_proxy"` -> `"Network / proxy"`.
- `_GITHUB_KEYS`: `tuple[str, ...]` — gains `"network_proxy"`.
- `_format_section` return: `str` (multi-line section text) — now contains a
  `Network / proxy` row instead of a raw `network_proxy` row.

## Verification (all must pass)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

## Definition of done

- `Network / proxy` label renders in the GITHUB section; no raw `network_proxy`
  key visible.
- `network_proxy` is in `_GITHUB_KEYS` and `test_all_github_keys_in_label_map`
  passes.
- pylint / pytest / mypy all pass; run `./tools/format_all.sh` before committing.

## LLM prompt

> Implement Step 1 as described in `pr_info/steps/step_1.md`, using
> `pr_info/steps/summary.md` for context. This is a single TDD commit for issue
> #993.
>
> 1. In `tests/cli/commands/test_verify_format_section_basic.py`
>    (`TestGitHubLabelMappings`): add `"network_proxy"` to the `_GITHUB_KEYS`
>    tuple (after `"api_base_url"`); make the `test_all_github_keys_in_label_map`
>    docstring count-agnostic ("All GitHub check keys exist in _LABEL_MAP.");
>    and extend the existing `test_format_section_renders_github_labels` with a
>    `network_proxy` entry plus assertions that `"Network / proxy"` appears,
>    `"network_proxy"` does not, `"[OK]"` is present, and `"[ERR]"` is present
>    (the failed `ok=False` probe renders `[ERR]`, per the issue rationale). Do
>    NOT add a new test method.
> 2. Run pytest and confirm the key-set test fails (label map entry missing).
> 3. In `src/mcp_coder/cli/commands/verify.py`, add
>    `"network_proxy": "Network / proxy",` to `_LABEL_MAP` immediately after the
>    `"api_base_url"` entry.
> 4. Run pylint, pytest (with the fast `-m "not ..."` exclusions and `-n auto`),
>    and mypy. Fix anything that fails.
> 5. Run `./tools/format_all.sh` and commit as one commit.
>
> Do not add severity-aware markers, do not expand the value across multiple
> lines, and do not bump any dependency — all out of scope per the summary.
