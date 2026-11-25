# Step 1 — Remove `gh-tool define-labels --config`

## LLM prompt

Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`. Write the test
changes first, then the implementation. Run pylint, mypy and the fast pytest set (see
CLAUDE.md), format the code, and produce exactly one commit.

## WHERE

- `src/mcp_coder/cli/gh_parsers.py` — `add_gh_tool_parsers`, the `define-labels` parser
- `src/mcp_coder/cli/commands/define_labels.py` — `execute_define_labels`
- `docs/cli-reference.md` — `### gh-tool define-labels` section (line ~617)
- `tests/cli/test_gh_parsers.py`
- `tests/cli/commands/test_define_labels.py`
- `tests/cli/commands/test_define_labels_summary.py`

## WHAT

### Tests first

`tests/cli/test_gh_parsers.py` (class `TestDefineLabelsParser`):
- `test_default_flags_are_false`: drop `assert args.config is None`.
- Replace `test_config_flag` with:
  ```python
  def test_config_flag_is_rejected(self, capsys: pytest.CaptureFixture[str]) -> None:
      """--config is not a define-labels flag."""
      with pytest.raises(SystemExit):
          self._parse("gh-tool", "define-labels", "--config", "x")
      assert "unrecognized arguments" in capsys.readouterr().err
  ```
  (add `import pytest`).
- `test_combined_flags`: remove `"--config", "my.json"` and `assert args.config == "my.json"`.

`tests/cli/commands/test_define_labels.py`:
- Delete `test_config_flag_passed_to_discovery`.
- `_make_namespace`: remove the `config` parameter and `config=config`.

`tests/cli/commands/test_define_labels_summary.py`:
- `_make_namespace`: remove the `config` parameter and `config=config`.

### Implementation

`gh_parsers.py`:
- Delete the `define_labels_parser.add_argument("--config", ...)` block.
- Delete the epilog block from `Config resolution:` through `3. Bundled package defaults`
  (keep the `--all` block as the epilog's last lines; the closing `"""` follows it).

`define_labels.py` (`execute_define_labels`):
- Delete the `# --config support` comment and the `config_override = ...` line.
- Change the call to `config_path = get_labels_config_path(project_dir)` (the parameter-less
  call follows in step 2). Keep the surrounding `try/except` and `validate_labels_config`.
- `Path` stays imported (used elsewhere in the module).

`docs/cli-reference.md`: delete the `- \`--config PATH\` selects the labels config. ...` bullet.
`tests/docs/test_cli_reference.py` fails while the doc lists a flag the parser lacks, so this
goes in the same commit.

## HOW

No new imports in source. `pytest` import in `test_gh_parsers.py` if missing.

## ALGORITHM

None — deletion only. argparse produces the "unrecognized arguments" error itself.

## DATA

`argparse.Namespace` for `define-labels` no longer has a `config` attribute.

## Done when

- `mcp-coder gh-tool define-labels --config x` → argparse error (test above).
- `grep -- "--config" src/mcp_coder/cli/gh_parsers.py` shows no define-labels entry.
- `tests/docs/` and `tests/cli/` pass; pylint and mypy clean.
