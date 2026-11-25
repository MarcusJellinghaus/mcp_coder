# Step 4 — Docs: bundled labels only

## LLM prompt

Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`. Steps 1–3 are
already committed. Docs only — no code changes. Run the `tests/docs/` tests and
`tests/cli/commands/test_define_labels_actions.py`, and produce exactly one commit.

## WHERE

- `docs/getting-started/label-setup.md`
- `docs/repository-setup/github.md`
- `docs/repository-setup/python.md`
- `docs/architecture/architecture.md`

## WHAT

Test-first does not apply (prose). The guard tests already exist:
`tests/docs/` and `test_define_labels_actions.py::test_doc_contains_generator_output`, which
requires the generated workflow YAML blocks in `label-setup.md` and `github.md` to stay
byte-identical. Do not touch any fenced `yaml` block.

### `docs/getting-started/label-setup.md`
- Replace the whole `## Label Configuration` section (its intro, `### Configuration Priority`,
  `### Configuration File Format`, `### Customizing Labels`) with:
  ```markdown
  ## Label Configuration

  The workflow labels come from the bundled `labels.json` that ships with mcp-coder. For the
  fields of a label (`default`, `promotable`, `failure`, categories, timeouts), see
  [`labels_schema.md`](../../src/mcp_coder/config/labels_schema.md).
  ```
- Command Options table: delete the `--config PATH` row.
- Examples: delete `# Use a custom config file` and the `--config config/labels.json` line
  (and the blank line before it, so no double blank remains).
- GitHub Actions tip: "from your label config" → "from the bundled labels"; "in your labels
  config" → "in the bundled labels".
- PR-Health paragraph: delete the sentence starting "A custom `labels-config` must add
  `merged` and `merge_failed` …".

### `docs/repository-setup/github.md`
- Rename `### Customizing Labels` → `### Label Source`. Keep the
  "**Default label source:** `mcp_coder/config/labels.json`, deployed with the package." line;
  replace everything else in the section (the "Custom labels" sentence, the `toml` snippet,
  the "Alternatively, pass `--config PATH` …" sentence and "Test custom config" with its bash
  block) with: "See [`labels_schema.md`](https://github.com/MarcusJellinghaus/mcp_coder/blob/main/src/mcp_coder/config/labels_schema.md) for the schema."
- Required Actions tip (line ~442): "based on your label config" → "based on the bundled
  labels".
- `### Stale Timeout Configuration`: "Bot-busy labels can have configurable timeout thresholds
  in `labels.json`:" → "Bot-busy labels in the bundled `labels.json` have timeout thresholds:".
  Reword any further "configurable" phrasing in that section the same way.

### `docs/repository-setup/python.md`
- Key Sections table: delete the `[tool.mcp-coder] labels-config` row.
- "mcp-coder-specific behavior" paragraph: delete the sentence "Label configuration
  (`labels-config`) is read by [`config/label_config.py`](…)."

### `docs/architecture/architecture.md`
- Label-driven state machine bullet: delete " (overridable per repo)".

## HOW / ALGORITHM / DATA

Not applicable (documentation).

## Done when

- `search_files` with pattern `labels-config|define-labels --config` in `docs/` and
  `README.md` finds nothing; `--config` no longer appears in `label-setup.md` or `github.md`.
- `tests/docs/` and `tests/cli/commands/test_define_labels_actions.py` pass.
