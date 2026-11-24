# Step 1 — `init` reads the toolkit: `python.md` only for `mcp-tools-py`, reminder otherwise

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`). Implement
> step 1 only: write the tests first, then the code, then the docs. Run the format, pylint,
> pytest (fast unit tests) and mypy checks from `.claude/CLAUDE.md`; all must pass. One
> commit: `feat(init): deploy python.md only for the mcp-tools-py toolkit`.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py`
- `src/mcp_coder/cli/commands/init.py`
- `tests/cli/commands/test_init.py`
- `docs/repository-setup/README.md`, `docs/cli-reference.md`,
  `docs/repository-setup/claude-code.md`

## WHAT

### `toolkit_runner.py`
- Rename `_PYTHON_TOOLKIT` → `PYTHON_TOOLKIT` (definition at the top, use in
  `_toolkit_class`). Use `rename_symbol`, or edit both places by hand.

### `init.py`
```python
from ...utils.toolkit_runner import PYTHON_TOOLKIT, load_toolkit_config

PYTHON_ONLY_FILE = Path("knowledge_base") / "python.md"  # relative to the source dir
_ADAPT_URL = (
    "https://github.com/MarcusJellinghaus/mcp_coder/blob/main/"
    "docs/repository-setup/README.md#adapting-deployed-files-non-python-repos"
)
_GENERIC_REMINDER = (
    "The deployed skills, agents and knowledge base are generic: map the checks, tests "
    "and formatting to your tools in .claude/CLAUDE.md, and adapt the agents' tools: "
    "and the skills' allowed-tools.",
    "Files that already existed were kept; delete them to get the new versions.",
    f"See {_ADAPT_URL}",
)

def _is_python_toolkit(project_dir: Path) -> bool: ...
def _deploy_skills(source_dir: Path, project_dir: Path, skip_python: bool = False) -> tuple[int, int]: ...
```
- Import `load_toolkit_config` from `utils.toolkit_runner` (not `toml_utils`): the autouse
  stub in `tests/conftest.py` patches `toolkit_runner.find_mcp_coder_table`.

## HOW / ALGORITHM

`_is_python_toolkit`:
```
try: name = load_toolkit_config(project_dir).toolkit
except ValueError as exc:
    logger.warning("%s", exc)     # error text already carries the no-toolkit help
    return False
return name == PYTHON_TOOLKIT
```

`_deploy_skills` loop: after computing `rel = src_file.relative_to(source_dir)`, add
`if skip_python and rel == PYTHON_ONLY_FILE: continue` (not counted as added or skipped).

`execute_init`, deploy branch only (the self-deploy skip stays untouched):
```
python = _is_python_toolkit(project_dir)
added, skipped = _deploy_skills(source_dir, project_dir, skip_python=not python)
logger.log(OUTPUT, "Skills: %d added, %d skipped", added, skipped)
if not python:
    for line in _GENERIC_REMINDER: logger.log(OUTPUT, line)
```
The return code is unchanged: the toolkit never makes `init` fail. `init` writes no
`mcp-coder.toml` / `pyproject.toml`.

## DATA

- `_is_python_toolkit` → `bool`.
- `_deploy_skills` → `(added, skipped)` as before; the skipped `python.md` counts in neither.

## Tests (write first) — `tests/cli/commands/test_init.py`

New class `TestInitToolkit`. Helper builds a source like `TestExecuteInitWithDeploy._make_source`
plus `knowledge_base/python.md`, monkeypatches `_find_claude_source_dir`, runs
`execute_init(argparse.Namespace(command="init", just_skills=True, project_dir=str(project)))`
under `caplog.at_level(logging.DEBUG)`.

1. `test_command_toolkit_skips_python_md_and_reminds` — root `mcp-coder.toml` with
   `[tool.mcp-coder.toolkit]\ntoolkit = "command"\n`. Assert exit 0, no
   `.claude/knowledge_base/python.md`, other files deployed, reminder text (e.g.
   `"are generic"` and `_ADAPT_URL`) in `caplog.text`.
2. `test_python_toolkit_deploys_python_md_without_reminder` — `pyproject.toml` with
   `toolkit = "mcp-tools-py"`. Assert exit 0, `python.md` deployed, `"are generic"` not in
   `caplog.text`.
3. `test_no_toolkit_warns_and_skips_python_md` — mark `@pytest.mark.real_toolkit_config`
   (else the stub injects `mcp-tools-py`); no config file. Assert exit 0, `python.md` not
   deployed, a WARNING record containing
   `No [tool.mcp-coder.toolkit] table in pyproject.toml or mcp-coder.toml.` and
   `toolkit = "command"`, and the reminder.

Existing tests stay unchanged: without a config, the autouse stub supplies `mcp-tools-py`.

## Docs

- `docs/repository-setup/README.md`: add after the "Quick Setup Checklist" section:
  ```
  ## Adapting Deployed Files (Non-Python Repos)

  `mcp-coder init` deploys generic skills, agents and knowledge base; it adds
  `.claude/knowledge_base/python.md` only with the `mcp-tools-py` toolkit. In any other repo,
  adapt:

  - `.claude/CLAUDE.md`: map formatting, checks and tests (and any dead-code or architecture
    checks) to your tools. The skills and agents refer to them by purpose.
  - Agents' `tools:` and skills' `allowed-tools`: they name `mcp__mcp-tools-py__*` tools;
    replace or remove them.
  - Knowledge base: add language notes for your stack if reviews should apply them.

  This is a reminder, not a complete list. `init` never overwrites: delete a deployed file
  to get its current version.
  ```
  In the files table, set the `.claude/knowledge_base/python.md` row's "What to adjust" to
  "Deployed only with the `mcp-tools-py` toolkit".
- `docs/cli-reference.md`, `### init`: after the `--just-skills` paragraph add a **Toolkit**
  paragraph: before deploying, init reads `[tool.mcp-coder.toolkit]`. `mcp-tools-py` →
  everything deployed. Any other toolkit → `knowledge_base/python.md` skipped and a reminder
  printed (link to the README section). Missing or invalid table → the config error is
  logged as a warning, then as for another toolkit; the toolkit never fails `init`.
- `docs/repository-setup/claude-code.md` line with `.claude/knowledge_base/python.md`: append
  "— deployed only with the `mcp-tools-py` toolkit".
