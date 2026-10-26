# Step 3 — `[github] trusted_commenters` config key

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md`
> only. TDD: add the tests first, then the code. Run pylint, mypy and the
> fast unit tests (see CLAUDE.md) until they pass, run `run_format_code`,
> and make exactly one commit.

## WHERE

- `src/mcp_coder/utils/user_config.py` (`_CONFIG_SCHEMA["github"]`,
  template string in `create_default_config`, `[github]` block ~line 290)
- `docs/configuration/config.md` (template copy ~line 77; new section under
  `## Configuration Sections`)
- `tests/utils/test_user_config_schema.py`
- `tests/utils/test_user_config_create_default.py`

## WHAT

- Schema: `"trusted_commenters": FieldDef(list),` in the `github` section —
  **no `env_var`** (mcp-workspace reads it from the file only).
- Template, under `[github]` after `token = ...` (same text in both
  `user_config.py` and the `config.md` template copy):

  ```toml
  # Extra logins whose PR/issue comments are trusted, besides repo
  # owners, members and collaborators (e.g. a CI machine user)
  # trusted_commenters = ["your-ci-bot"]
  ```

- `config.md`: add `### [github]` under `## Configuration Sections` with a
  Field / Type / Description table: `token` (str), `test_repo_url` (str),
  `trusted_commenters` (list of str — extra trusted logins; link to
  https://github.com/MarcusJellinghaus/mcp-workspace#github-configuration).
  Mention that this key has no environment-variable override.

## HOW

No code paths read the key in mcp-coder; mcp-workspace's
`get_trusted_commenters()` reads it. The schema entry only makes `verify`
recognise it (expected new info row: `[github] trusted_commenters not
configured`).

## ALGORITHM

None.

## DATA

`FieldDef(field_type=list, required=False, env_var=None)`.

## Tests

- `test_user_config_schema.py`: `_CONFIG_SCHEMA["github"]["trusted_commenters"]`
  has `field_type is list` and `env_var is None`.
- `test_user_config_create_default.py`: generated file contains
  `# trusted_commenters` and still parses with `tomllib`.
- Run the full fast suite; if a verify test pins the `[github]` row count,
  update it for the new info row.
