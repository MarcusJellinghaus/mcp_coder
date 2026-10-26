# Step 1 — Generator: pin, permissions, trust gate, separator (TDD)

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`. Write the tests first, watch them fail, then change the generator. Change only the files listed under WHERE. Run pylint, pytest (`-n auto`, unit markers), mypy and `run_format_code`; all must pass. Produce one commit.

## WHERE
- `src/mcp_coder/cli/commands/define_labels_actions.py`
- `tests/cli/commands/test_define_labels_actions.py`

## WHAT

### Generator
- New module constant, placed after `logger`:
  ```python
  _GITHUB_SCRIPT_REF = (
      "actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0"
  )
  ```
- `generate_label_new_issues_yml(default_label_name: str) -> str`:
  - add top-level `permissions: {{}}` (f-string escaping) between the `on:` block and `jobs:`;
  - change the step to `uses: {_GITHUB_SCRIPT_REF}`.
- `generate_approve_command_yml(promotions: list[tuple[str, str]]) -> str`:
  - add the same top-level `permissions: {{}}`;
  - change `uses:` to `{_GITHUB_SCRIPT_REF}`;
  - set the job `if:` to:
    ```
    if: github.event.issue.pull_request == null && contains(github.event.comment.body, '/approve') && contains(fromJSON('["OWNER","MEMBER","COLLABORATOR"]'), github.event.comment.author_association)
    ```
  - replace the comment above it with:
    `# Only run on issues (not PRs), when comment contains /approve, and only for trusted commenters (OWNER/MEMBER/COLLABORATOR); untrusted -> skipped silently`
  - in the success comment, change the separator before `The bot` from `\\n` to `\\n\\n` (the rendered JS string reads `` ...\`${newStatus}\`\n\nThe bot can now... ``);
  - keep the exact-match `/approve` check in the script unchanged.

Signatures are unchanged. No other edits to the templates: blank script lines stay empty, and the generator keeps the trailing comma on the last promotion.

### Tests (add to `test_define_labels_actions.py`)
```python
import re

_USES_RE = re.compile(r"^\s*(?:- )?uses:")
_PIN_RE = re.compile(r"^\s*(?:- )?uses: [\w.\-/]+@[0-9a-f]{40} # v\d")

def _generated_workflows() -> dict[str, str]:  # name -> YAML text
    return {
        "label-new-issues.yml": generate_label_new_issues_yml("status-01:created"),
        "approve-command.yml": generate_approve_command_yml(
            [("status-01:created", "status-02:awaiting-planning")]
        ),
    }
```
- `@pytest.mark.parametrize("name", ["label-new-issues.yml", "approve-command.yml"])`
  - `test_top_level_permissions_empty(name)`: `yaml.safe_load(content)["permissions"] == {}`
  - `test_uses_sha_pinned(name)`: collect the `uses:` key lines (match `_USES_RE`, not a plain substring, since the approve script's error message contains `statuses:`); there is at least one, and each one matches `_PIN_RE`
- In `TestGenerateApproveCommandYml`, `test_job_gated_on_author_association`:
  - `cond = parsed["jobs"]["handle-approve"]["if"]`
  - assert `"github.event.comment.author_association" in cond`
  - assert `"fromJSON('[\"OWNER\",\"MEMBER\",\"COLLABORATOR\"]')" in cond`
- `test_success_comment_separator`: `"\\n\\nThe bot can now pick up" in content` (raw generator text)

## HOW
- No new imports in the generator. The tests add `import re`.
- The parametrized tests can be module-level functions or a small class `TestGeneratedWorkflowHardening`; match the file's class style.

## ALGORITHM (SHA-pin test)
```
content = _generated_workflows()[name]
uses_lines = [l for l in content.splitlines() if _USES_RE.match(l)]
assert uses_lines
for line in uses_lines:
    assert _PIN_RE.match(line), line
```

## DATA
- Generator returns: YAML `str`, unchanged in type.
- Parsed YAML: `parsed["permissions"] == {}`; `parsed["jobs"]["handle-approve"]["if"]` is a `str`.

## Notes
- The committed `.github/workflows/*.yml` files are **not** regenerated in this step (that is step 2), so no test compares against them yet.
