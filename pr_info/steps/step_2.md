# Step 2 — Declare and document `[github] traffic_log` / `traffic_log_dir`

## LLM prompt
> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_2.md`).
> Implement only Step 2. Tests first, then code and docs.
> Run pylint, pytest (fast unit marker set, `-n auto`) and mypy; all must pass.
> Produce exactly one commit.

## WHERE
- `src/mcp_coder/utils/user_config.py` (`_CONFIG_SCHEMA["github"]`, config template string under `[github]`)
- `docs/configuration/config.md` (`[github]` table, example, template copy near line 79)
- `tests/utils/test_user_config_schema.py`, `tests/utils/test_user_config_create_default.py`

## WHAT
- Schema: add to `"github"`:
  ```python
  "traffic_log": FieldDef(bool),
  "traffic_log_dir": FieldDef(str),
  ```
  No `env_var`. mcp_coder does not read these keys itself — mcp-workspace does.
- Template (after the `trusted_commenters` lines):
  ```toml
  # GitHub traffic log (read by mcp-workspace; opt-in, only `true` enables it)
  # traffic_log = true
  # traffic_log_dir = "~/.mcp_coder/logs/github_traffic"
  ```
- Docs: two rows in the `[github]` table and the commented lines in the example:
  - opt-in, only boolean `true` enables it;
  - default dir `~/.mcp_coder/logs/github_traffic/`, files `github_requests_YYYY-MM-DD.log`;
  - no env var; read by mcp-workspace once per process;
  - line format: link `https://github.com/MarcusJellinghaus/mcp-workspace#github-traffic-log`
    (do not copy the format).

## HOW
Tests (TDD):
- schema test: `_CONFIG_SCHEMA["github"]["traffic_log"].field_type is bool`,
  `traffic_log_dir` is `str`, both `env_var is None`.
- template test: the created default config text contains `# traffic_log = true`
  and `# traffic_log_dir`.

## DATA
No runtime behaviour change.
