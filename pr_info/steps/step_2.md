# Step 2 — Create `.github/workflows/upstream-mypy-check.yml`

> Read `pr_info/steps/summary.md` first for full context. This step is independent of Step 3 and creates a new workflow file.

## Goal

Add a listener-only workflow that re-runs `mypy --strict` against this repo whenever any of the three upstream packages updates `main` (via `repository_dispatch`). Also supports manual `workflow_dispatch` for testing.

## WHERE

- **Create** new file: `.github/workflows/upstream-mypy-check.yml`

No other files modified in this step.

## WHAT

Exact file content (matches the issue spec verbatim):

```yaml
name: Upstream mypy check

# Triggered by repository_dispatch when an upstream package's main branch changes.
# Upstream packages: mcp-coder-utils, mcp-workspace, mcp-tools-py.
# Runs mypy --strict against the latest main of all three to detect interface breaks.
# On failure: standard GitHub Actions email + red icon in the Actions tab.

on:
  repository_dispatch:
    types: [upstream-main-updated]
  workflow_dispatch:
    inputs:
      upstream:
        description: 'Upstream that triggered this run (shown in the job name)'
        required: false
        default: 'manual'

permissions:
  contents: read

jobs:
  mypy-against-upstream-main:
    name: mypy-against-upstream-${{ github.event.client_payload.upstream || github.event.inputs.upstream || github.event_name }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v7
      - uses: actions/setup-python@v6
        with:
          python-version: 3.11

      # Order matters: install upstream packages from git BEFORE `.[typecheck]`
      # so uv's resolver doesn't replace them with PyPI versions. The base
      # pyproject.toml has no version pins on these three packages, so any
      # already-installed version satisfies the constraint.
      - name: Install upstream packages from main
        run: |
          uv pip install --system "mcp-coder-utils @ git+https://github.com/MarcusJellinghaus/mcp-coder-utils.git"
          uv pip install --system "mcp-workspace @ git+https://github.com/MarcusJellinghaus/mcp-workspace.git"
          uv pip install --system --no-deps "mcp-tools-py @ git+https://github.com/MarcusJellinghaus/mcp-tools-py.git"

      - name: Install mcp_coder with typecheck extra
        run: uv pip install --system ".[typecheck]"

      - name: Run mypy --strict
        run: mypy --strict src tests
```

## HOW

- File goes alongside the other workflow files in `.github/workflows/`.
- No matrix — single job, single Python version (3.11) — keeps signal clear and feedback fast.
- `permissions: contents: read` — the workflow only reads code; no write tokens needed (no PAT secret required, per the issue).
- The install-order comment block is **load-bearing** — do not collapse or paraphrase it. It guards future maintainers from reordering the two `pip install` steps.

## ALGORITHM (workflow logic)

```
1. Trigger: repository_dispatch (type=upstream-main-updated) OR workflow_dispatch.
2. Checkout this repo at HEAD of triggering ref.
3. Set up uv + Python 3.11.
4. uv pip install (with deps) the two stable upstreams from git+main.
5. uv pip install --no-deps the third upstream from git+main (avoids dragging in dev deps).
6. uv pip install ".[typecheck]" — adds mypy + stubs without disturbing step 4-5.
7. Run `mypy --strict src tests`. Non-zero exit -> red badge + email.
```

## DATA

- **Triggers:** `repository_dispatch` with `client_payload.upstream` (string), or `workflow_dispatch` with `inputs.upstream` (string, default `"manual"`).
- **Job name format:** `mypy-against-upstream-{client_payload.upstream || inputs.upstream || github.event_name}` — fallback chain ensures it's never empty.
- **Outputs:** standard GitHub Actions run status (success/failure); no artifacts.

## Verification

YAML changes don't trigger Python checks meaningfully, but per CLAUDE.md, still run all three after the edit (they should be no-ops):

```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__tools-py__run_pylint_check
mcp__tools-py__run_mypy_check
```

Optional sanity check — confirm the workflow file is present and well-formed using only the stdlib (`pyyaml` is not in any extra of this repo):

```bash
python -c "from pathlib import Path; assert Path('.github/workflows/upstream-mypy-check.yml').read_text().startswith('name:'), 'workflow file missing name: header'"
```

GitHub itself validates the YAML on push, so this is a soft smoke test only.

The actual `workflow_dispatch` smoke test (acceptance criterion 4) is performed by the user in the GitHub Actions UI **after** the PR merges — call it out in the PR description.

## Commit

One commit:
```
Add upstream-mypy-check workflow (issue #922)

Listener-only workflow: re-runs mypy --strict against this repo whenever
an upstream package (mcp-coder-utils / mcp-workspace / mcp-tools-py)
updates main, via repository_dispatch. Also supports manual
workflow_dispatch for ad-hoc verification. Includes install-order
comment guarding the upstream-from-git -> .[typecheck] sequence.
```

## LLM prompt for this step

> Implement Step 2 of `pr_info/steps/summary.md`. Read both `pr_info/steps/summary.md` and `pr_info/steps/step_2.md` for full context.
>
> Create the file `.github/workflows/upstream-mypy-check.yml` with the exact content shown in step_2.md. Preserve the install-order comment verbatim — it guards a non-obvious resolver behavior. Do not modify any other files in this step.
>
> Use only MCP tools. After creating the file, run the three required quality checks. Make exactly one commit with the message in step_2.md.
