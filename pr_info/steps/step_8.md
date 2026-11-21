# Step 8 — `python` extra; delete the wrapper (Scope 2)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_8.md`).
> Implement Step 8 only: delete `src/mcp_coder/mcp_tools_py.py` and its test,
> move mcp-tools-py into the `python` extra, and update `.importlinter`,
> `tach.toml`, deptry config, the upstream-compat workflow, the rebase binding
> test and the architecture docs — all in this one commit (import-linter fails
> on any leftover entry). Run format, pylint, mypy, lint-imports, tach, deptry
> and the fast pytest set. One commit.

## Precondition

`search_files(pattern="mcp_tools_py import|import mcp_tools_py|from \.\.\.mcp_tools_py|from \.\.mcp_tools_py|mcp_coder\.mcp_tools_py", glob="src/**/*.py")`
must match only `src/mcp_coder/mcp_tools_py.py` itself (Step 7 removed the
`verify_sections` import). If anything else matches, write one line to
`pr_info/.blocked.txt` and stop.

## WHERE / WHAT

- Delete `src/mcp_coder/mcp_tools_py.py` and `tests/test_mcp_tools_py.py`.
- `pyproject.toml`:
  - `dependencies`: remove `"mcp-tools-py"`.
  - `[project.optional-dependencies]`: add
    ```toml
    # Python toolkit (PythonToolkit via the mcp_coder.toolkits entry point) and its checkers
    python = ["mcp-tools-py"]
    ```
    and `dev = ["mcp-coder[types,test,langchain,mlflow,tui,python]", ...]`.
  - `[tool.deptry.per_rule_ignores]`: add
    `DEP002 = ["mcp-tools-py"]` with a comment: reached only through the
    entry point; deptry doesn't expand the `mcp-coder[...]` self-reference.
  - Keep mcp-tools-py in `[tool.mcp-coder.install-from-github]` and in
    `post_install_checks`.
- `.importlinter`:
  - layers contract (line ~45): `mcp_coder.mcp_tools_py | mcp_coder.mcp_workspace_git | ...`
    → `mcp_coder.mcp_workspace_git | mcp_coder.mcp_workspace_github`
  - `toolkits_isolation` source list (line ~167): remove `mcp_coder.mcp_tools_py`
  - `mcp_checker_isolation`: delete the `ignore_imports` key and its line;
    comment → "The 'mcp_tools_py' package is never imported by mcp_coder:
    PythonToolkit is reached only through the mcp_coder.toolkits entry point."
- `tach.toml`: remove the `[[modules]]` block `path = "mcp_coder.mcp_tools_py"`
  and both `depends_on` entries naming it (lines ~69, ~497).
- `.github/workflows/upstream-compat-check.yml`: extras
  `.[typecheck,test,langchain]` → `.[typecheck,test,langchain,python]`.
- `tests/workflows/rebase/test_command_toolkit_binding.py`: remove the patch of
  `mcp_coder.mcp_tools_py.__all__`; the test must not reference the wrapper.
  Keep its `command` toolkit assertions.
- Architecture docs naming the wrapper (hand edits; no regeneration):
  `tools/tach_docs.py` (hard-coded diagram), `docs/architecture/dependencies/dependency_graph.html`,
  `docs/architecture/dependencies/pydeps_graph.dot`, `pydeps_graph.html`,
  `docs/architecture/architecture.md`, `docs/architecture/enforcement.md`.
  Find them with `search_files(pattern="mcp_tools_py")` over `docs/` and `tools/`.

## HOW

Run the uv/pip install only if the environment needs it — it already has
mcp-tools-py (dev install). `mcp-tools-py` registers the `mcp-tools-py`
entry point itself.

## ALGORITHM

None (config and deletion).

## DATA

None.

## Tests

- Existing suite stays green; `run_lint_imports_check`, `run_tach_check` and
  `run_deptry_check` pass.
- `search_files(pattern="mcp_tools_py", glob="src/**/*.py")` → no match.
