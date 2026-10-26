# Step 2 — Regenerate committed workflows, replace doc snippets, consistency test

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`. Write the consistency test first and watch it fail, regenerate the committed workflows with a scratch probe, then replace the doc snippets. Delete `.scratch/` before committing. Run pylint, pytest (`-n auto`, unit markers), mypy and `run_format_code`; all must pass. Produce one commit.

## WHERE
- `tests/cli/commands/test_define_labels_actions.py` (new test class)
- `.github/workflows/approve-command.yml`, `.github/workflows/label-new-issues.yml` (regenerated)
- `docs/repository-setup/github.md` § "GitHub Actions Setup" (both YAML blocks plus the tip)
- `docs/getting-started/label-setup.md` § "GitHub Actions Setup" (both YAML blocks plus the tip)

## WHAT

### Consistency test
```python
from mcp_coder.config.label_config import get_labels_config_path, load_labels_config

REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW_NAMES = ["label-new-issues.yml", "approve-command.yml"]
_DOC_FILES = ["docs/repository-setup/github.md", "docs/getting-started/label-setup.md"]

class TestGeneratedWorkflowsConsistency:
    @pytest.fixture
    def generated(self, tmp_path: Path) -> dict[str, str]: ...
    @pytest.mark.parametrize("name", _WORKFLOW_NAMES)
    def test_committed_workflow_matches_generator(self, generated, name) -> None: ...
    @pytest.mark.parametrize("doc", _DOC_FILES)
    @pytest.mark.parametrize("name", _WORKFLOW_NAMES)
    def test_doc_contains_generator_output(self, generated, doc, name) -> None: ...
```

## ALGORITHM
```
config = load_labels_config(get_labels_config_path(REPO_ROOT))   # -> bundled labels.json
write_github_actions(tmp_path, config)                             # reuse the real writer
generated = {n: (tmp_path/".github/workflows"/n).read_text(encoding="utf-8") for n in names}
committed: (REPO_ROOT/".github/workflows"/name).read_text(encoding="utf-8") == generated[name]
docs:      generated[name] in (REPO_ROOT/doc).read_text(encoding="utf-8")
```
Compare with `read_text` (universal newlines), never bytes: Windows checkouts may be CRLF.

### Regeneration (scratch probe, deleted afterwards)
`.scratch/test_regen.py`:
```python
from pathlib import Path
from mcp_coder.cli.commands.define_labels_actions import write_github_actions
from mcp_coder.config.label_config import get_labels_config_path, load_labels_config

def test_regen() -> None:
    root = Path(__file__).resolve().parents[1]
    write_github_actions(root, load_labels_config(get_labels_config_path(root)))
```
Run it with `run_pytest_check(extra_args=["-p", "no:cacheprovider", ".scratch/test_regen.py"])`, then `delete_directory(".scratch", recursive=True)`. Do **not** run the `define-labels` CLI, because it syncs labels to GitHub.

Expected diff in `approve-command.yml`:
- top-level `permissions: {}`, the gate in `if:` plus the new comment, and the SHA-pinned `uses:`;
- blank script lines lose their trailing whitespace;
- `'status-07:code-review': 'status-08:ready-pr',` gains a trailing comma.

The success message is unchanged (`\n\nThe bot`).

Expected diff in `label-new-issues.yml`: `permissions: {}` and the pinned `uses:`.

### Doc snippets (both doc files)
- Replace the content of each ```` ```yaml ```` block under "Auto-Label New Issues" / "Approve Command Handler" with the **exact** text of the regenerated committed file. Keep the fences; the generated content ends with `\n`, then the closing fence.
- After the existing generator tip, add:
  > Existing repositories: re-run `mcp-coder gh-tool define-labels --generate-github-actions` to pick up the `/approve` trust gate, `permissions: {}` and the pinned action.
- Leave the surrounding prose ("Purpose:", "This handles…") as is. Do not touch the Code Quality CI example (`@v4`) in `github.md`.

## DATA
- `generated`: `dict[str, str]` mapping the workflow file name to its YAML text.

## Precondition
- If the regenerated `approve-command.yml` promotions differ from `status-01→02`, `04→05`, `07→08`, write one line to `pr_info/.blocked.txt` and stop.
