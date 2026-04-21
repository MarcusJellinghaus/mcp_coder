# mcp-suite Mono-Repo Plan — Alternative to mcp-utils Extraction

Companion to `mcp_utils_plan.md`. That plan extracts a shared `mcp-utils` library across 4 repos. This plan asks the opposite question: **what if we collapse the 4 repos into one?**

Nothing here is committed. This is a decision-support doc so we can compare the mono-repo path against the multi-repo extraction path before choosing.

---

## 0. Why consider a mono-repo

Cross-repo pain points surfaced by `mcp_utils_plan.md`:

1. **Release coupling (open question in §Cross-cutting).** Touching `subprocess_runner` means: PR on mcp-utils → tag → bump in 4 consumers → 4 more PRs. Per-module. Explicitly noted as "acceptable, or push toward monorepo?"
2. **Cross-repo refactors have no atomic unit.** GitHub has no cross-repo PR. The plan's own §"Planning and implementation process" admits coordination is manual (tracking issue in mcp_coder + thin per-repo issues + serial PR sequence + manual grep across 4 repos to verify no stale imports).
3. **Shim layer exists only because of repo boundaries.** Every cross-repo dep goes through a thin wrapper (`mcp_coder/mcp_tools_py.py`, `mcp_coder/mcp_workspace.py`) per rule. In one repo these shims simply vanish — call sites import the function.
4. **Duplication is the default, dedupe requires ceremony.** `subprocess_runner` exists in 3 repos with drift. `log_utils` exists in 3 repos with drift. `file_utils` is literally identical in 2 repos. Each dedupe needs a coordinated multi-PR dance. In one repo, duplication is a code-review comment.
5. **Tooling is replicated 4×.** Four `pyproject.toml`, four `.importlinter`, four `tach.toml`, four CI configs, four vulture whitelists, four `docs/repository-setup/` copies, four `CLAUDE.md` files. Drift between them is a known problem (`docs/repository-setup/` exists partly to fight it).
6. **LLM context fragmentation.** To reason about a change that touches `mcp_coder` workflows + `mcp_workspace` git tools, the LLM must use reference-project mechanisms to read a second repo. In a mono-repo it just opens the file.

**When mono-repo is the wrong answer:** when the 4 repos have genuinely different release cadences, different audiences, or different license/ownership boundaries. None of those apply here — same author, same audience (this project + a few downstream users), same release rhythm, same license.

---

## 1. Proposed layout

Three realistic options. I recommend **Option B**.

### Option A — Single distribution, single namespace

```
mcp_suite/
├── pyproject.toml            # one distribution: mcp-suite
└── src/mcp_suite/
    ├── coder/                # ex-mcp_coder (CLI, workflows, LLM, icoder)
    ├── tools_py/             # ex-mcp_tools_py (MCP server: checks, formatter, refactoring)
    ├── workspace/            # ex-mcp_workspace (MCP server: file ops, git, github)
    ├── config/               # ex-mcp_config (CLI: MCP client config)
    └── utils/                # ex-proposed mcp-utils (subprocess, logging, fs)
```

- **Pro:** Dead simple. One `pip install mcp-suite`. One version. Zero release coupling.
- **Con:** Users who only want the MCP server `mcp-workspace` get all of mcp_coder's deps (langchain, textual, mlflow, pygithub, jenkins…). Install footprint explodes.
- **Verdict:** Rejected. The deps of mcp_coder are far heavier than what an MCP server alone needs. Mixing them forces every downstream MCP server user to install everything.

### Option B — uv/hatch workspace, multi-package ⭐ recommended

```
mcp_suite/                           # repo root
├── pyproject.toml                   # workspace root: shared tool config + uv workspace
├── .importlinter                    # workspace-wide contracts (one file, many layers)
├── tach.toml                        # workspace-wide module boundaries
├── .github/workflows/ci.yml         # single CI with matrix per package
├── docs/                            # unified docs (architecture, repository-setup, …)
├── tools/                           # unified tools/ (format_all, lint_imports, …)
└── packages/
    ├── mcp-utils/                   # leaf lib (subprocess, logging, fs)
    │   ├── pyproject.toml
    │   ├── src/mcp_utils/
    │   └── tests/
    ├── mcp-tools-py/                # MCP server: Python ecosystem
    │   ├── pyproject.toml           # depends on mcp-utils (workspace = "*")
    │   ├── src/mcp_tools_py/
    │   └── tests/
    ├── mcp-workspace/               # MCP server: file ops + git + github
    │   ├── pyproject.toml           # depends on mcp-utils
    │   ├── src/mcp_workspace/
    │   └── tests/
    ├── mcp-config/                  # CLI: MCP client config
    │   ├── pyproject.toml           # depends on mcp-utils
    │   ├── src/mcp_config/
    │   └── tests/
    └── mcp-coder/                   # CLI: workflows, LLM, icoder, coordinator
        ├── pyproject.toml           # depends on mcp-utils + mcp-tools-py + mcp-workspace
        ├── src/mcp_coder/
        └── tests/
```

- **Distributions stay separate.** PyPI still sees 5 packages. Install footprint unchanged (`pip install mcp-workspace` still gives just mcp-workspace + mcp-utils).
- **Workspace tooling** (`uv` since 0.4, or `hatch` workspaces, or `poetry` workspaces) installs all packages in editable mode from the single repo. `pip install -e packages/mcp-coder` inside the workspace resolves `mcp-utils` to the sibling source, not PyPI.
- **One version, one tag.** Each release tags `vX.Y.Z` at the repo root and publishes all 5 distributions with that version. No more "bump mcp-utils, then bump 4 consumers." One PR, one merge, one tag.
- **Shared tool config** lives at the root (`pyproject.toml` `[tool.black]`, `[tool.isort]`, `[tool.ruff]`, `[tool.mypy]`). Per-package pyproject.toml only declares distribution metadata + deps + entry points.
- **Atomic cross-package refactors.** Renaming a function in `mcp-utils` and updating all callers in `mcp-coder`/`mcp-workspace` is one PR. Today it's 5 PRs serialized over a release cycle.
- **Con:** Workspace tooling is slightly less familiar than plain pip. uv handles this cleanly; hatch and poetry also work.

### Option C — Single distribution, multiple top-level packages

```
src/
├── mcp_utils/
├── mcp_tools_py/
├── mcp_workspace/
├── mcp_config/
└── mcp_coder/
```

One pyproject.toml, one distribution `mcp-suite`, multiple top-level importable packages. Optional extras control what gets pulled in (`mcp-suite[server]`, `mcp-suite[cli]`).

- **Pro:** Simpler than B (no workspace tooling). One dist to publish.
- **Con:** You can't install just `mcp-workspace` without mcp-coder's heavy deps unless you thread everything through optional extras, which turns into a combinatorial mess fast. Also: breaks `mcp-config` as an independently-installable CLI for users who don't use mcp-coder at all.
- **Verdict:** Works technically, loses packaging flexibility. Pick B instead.

---

## 2. Entry points — CLIs and MCP servers

The monorepo must preserve all current entry points. Inventory:

### CLIs (console scripts)

| Command | Current repo | Current entry | In monorepo (Option B) |
|---|---|---|---|
| `mcp-coder ...` | mcp_coder | `mcp_coder.cli.main:main` | `packages/mcp-coder/pyproject.toml` `[project.scripts]` — unchanged |
| `mcp-config ...` | mcp_config | (from mcp_config CLI) | `packages/mcp-config/pyproject.toml` `[project.scripts]` — unchanged |
| `icoder` | mcp_coder | `mcp-coder icoder` (self-sufficient) | stays in `packages/mcp-coder/` |

Each package declares its own `[project.scripts]`. `pip install mcp-coder` gives `mcp-coder` + `icoder`. `pip install mcp-config` gives `mcp-config`. Exactly as today.

### MCP server entry points

MCP servers are discovered by Claude Code / Claude Desktop / VS Code via `.mcp.json` config files that point at a Python entrypoint. Inventory:

| Server | Current repo | Current invocation | In monorepo (Option B) |
|---|---|---|---|
| `mcp-tools-py` | mcp_tools_py | `python -m mcp_tools_py` (or console script registered in its pyproject) | `packages/mcp-tools-py/pyproject.toml` declares it — unchanged |
| `mcp-workspace` | mcp_workspace | `python -m mcp_workspace` (idem) | `packages/mcp-workspace/pyproject.toml` — unchanged |

**Key point:** MCP server registration is per-package, not per-repo. Moving a package from its own repo into `packages/mcp-tools-py/` inside the workspace does not change the server's `main`/`server.py` entry, does not change the wheel it produces, does not change how `.mcp.json` references it. Downstream consumers who pin `mcp-tools-py` in their `.mcp.json` see zero change — they still `pip install mcp-tools-py` from PyPI and still invoke it the same way.

### `.mcp.json` files in the monorepo itself

The current mcp_coder repo ships `.mcp.json` + `.mcp.{linux,windows,macos}.json` that point at sibling MCP servers installed in a separate "tool venv". In the monorepo, those configs continue to point at installed versions — nothing in `.mcp.json` needs to know that the source now lives in the same repo. Dev iteration is faster because `pip install -e packages/mcp-tools-py` makes local edits immediately visible to the tool venv.

### `mcp-coder install-from-github` feature

Today `pyproject.toml` declares `[tool.mcp-coder.install-from-github]` with git URLs for sibling MCP servers, so users can install them from source. Post-monorepo this becomes a single entry: one git URL + a package-name list. The `get_github_install_config` helper stays where the extraction plan put it (mcp_coder, Phase 0 finding #1), it just reads a simpler config.

---

## 3. Architecture tools

The existing architecture tooling (import-linter, tach, pycycle, vulture, pydeps, ruff) is today configured **per repo**. In the monorepo it becomes **workspace-wide** — which is both simpler to maintain and more powerful (it can enforce rules *across* packages that today can't be expressed at all).

### Layering rules (enforced by tach + import-linter)

The mcp-utils extraction plan already defined the dependency graph. Codify it as tach layers:

```toml
# tach.toml (workspace root)
[[modules]]
path = "mcp_utils"
depends_on = []            # leaf — no internal deps

[[modules]]
path = "mcp_tools_py"
depends_on = ["mcp_utils"]

[[modules]]
path = "mcp_workspace"
depends_on = ["mcp_utils"]

[[modules]]
path = "mcp_config"
depends_on = ["mcp_utils"]

[[modules]]
path = "mcp_coder"
depends_on = ["mcp_utils", "mcp_tools_py", "mcp_workspace"]
# NOTE: mcp_coder does NOT depend on mcp_config (separate CLI, separate audience)
```

Import-linter mirrors this with contracts that fail CI if anyone imports "upward" (e.g. `mcp_utils` importing from `mcp_coder`).

**What this buys us that today's per-repo configs cannot:** today, nothing mechanically prevents `mcp_workspace` from importing `mcp_coder` because the two repos don't know about each other — the rule exists only in reviewer memory. In the monorepo a single contract makes it a CI failure.

### Other tools

| Tool | Today | Monorepo |
|---|---|---|
| `import-linter` | `.importlinter` per repo, 19 contracts in mcp_coder alone | Single `.importlinter` at root. Contracts reference all 5 packages |
| `tach` | `tach.toml` per repo | Single `tach.toml` at root, see above |
| `pycycle` | Per-repo scan | Single workspace scan |
| `vulture` | `vulture_whitelist.py` per repo | Single whitelist (or per-package if false positives cluster) |
| `pydeps` | Per-repo graph | Single cross-package graph — finally shows the full picture in one image |
| `ruff` | Per-repo config | Single `[tool.ruff]` at root |
| `black` / `isort` / `mypy` | Per-repo config, drifted line-lengths historically | Single root config, no drift possible |

### tools/ scripts

Current mcp_coder ships `tools/format_all.sh`, `tools/lint_imports.sh`, `tools/tach_check.sh`, etc. In the monorepo these live at the workspace root and operate across all packages by default. No per-package copies.

---

## 4. `docs/repository-setup/` — template consolidation

Today `docs/repository-setup/` in mcp_coder serves as a **template** that downstream projects manually copy files from (`.claude/`, `.mcp.json`, `.github/workflows/`, `pyproject.toml` references, tach configs, etc.). The README explicitly says "there is currently no sync/versioning mechanism — when files in this repo change, downstream projects must re-pull manually."

The mono-repo changes this picture in two ways:

### 4.1 Internal consumers disappear

The 5 packages in the workspace all share **one** `.claude/`, **one** `.mcp.json`, **one** set of CI workflows, **one** `tach.toml`, etc. — at the workspace root. The "repository setup" problem *between the 5 packages* goes away entirely.

### 4.2 External consumers still need templates

Downstream projects that use `mcp-coder` workflows still need the same set of starter files. So `docs/repository-setup/` remains useful — but its role shifts from "internal config plus template" to "pure template for external projects."

Proposed restructure:

| Path | Today | Monorepo |
|---|---|---|
| `.claude/CLAUDE.md`, `.mcp.json`, etc. | In mcp_coder root, *also* documented under `docs/repository-setup/` for template use | Lives at workspace root (actual config used by the 5 packages). `docs/repository-setup/` references them as "this is the template, copy from workspace root" |
| `docs/repository-setup/claude-code.md` | How-to for downstream | Unchanged in content, but points at the canonical files at workspace root |
| `docs/repository-setup/python.md` | Python-specific setup for downstream | Unchanged |
| `docs/repository-setup/internal.md` | "mcp-coder repo internals" | Repurposed as "mcp-suite monorepo internals" (workspace layout, how to add a package, release flow) |

**No new sync mechanism.** Downstream still pulls manually. But because the template files are *also* the files running the monorepo itself, drift between "what we ship as template" and "what we actually use" drops to zero by construction.

---

## 5. Cross-cutting concerns

### 5.1 CI / CD

- **Single `ci.yml`** with a matrix over the 5 packages. Each package's tests run in parallel. Shared jobs for workspace-wide checks (tach, import-linter, ruff).
- **Changed-files filter** (GitHub Actions `dorny/paths-filter` or equivalent) to skip packages when their files + deps are unchanged. E.g. touching only `mcp-config/` skips the mcp-coder test matrix.
- **Release workflow**: single `publish.yml` that on tag `vX.Y.Z` builds and publishes all 5 packages to PyPI with that version. setuptools-scm (already used by mcp_coder) reads the tag.

### 5.2 Versioning

- **Locked versions.** All 5 packages always have the same version. Released together. No independent cadence.
- **Why this is fine for us:** we already release them in lock-step de facto whenever cross-repo work happens — the extraction plan's entire Phase 3 is about this synchronization pain. Making it official removes the pain.
- **If we ever need independent releases:** uv workspace supports per-package versions; we can branch off that path later. Not needed day one.

### 5.3 Test markers

The current `pyproject.toml` defines 10+ pytest markers (`git_integration`, `github_integration`, `claude_cli_integration`, …). In the monorepo these move to the **root** pyproject and apply across all packages. No duplication of marker definitions.

### 5.4 Dependencies

Per-package `pyproject.toml` declares its own runtime deps. Shared tool deps (black, isort, mypy, pylint, ruff, vulture, tach, import-linter, pydeps) move to the **root** as workspace dev-dependencies. Installed once for the whole workspace.

### 5.5 LLM context / CLAUDE.md

- **Single root `CLAUDE.md`.** Today's CLAUDE.md is already 200+ lines; it does not need to be duplicated 5×.
- **Per-package `CLAUDE.md` (optional).** Only if a package has genuinely different conventions (unlikely given everything is the same author).
- **No more "Shared libraries" block + reference-project indirection.** The extraction plan needs those because `mcp-utils` lives in a separate repo that the LLM must be pointed at. In the monorepo the LLM just reads `packages/mcp-utils/src/...` directly.

### 5.6 Shims disappear

`mcp_coder/mcp_tools_py.py` and `mcp_coder/mcp_workspace.py` are thin shims that exist purely to document + centralize cross-repo imports (per the extraction plan's shim rule). In the monorepo they're unnecessary — call sites can import directly from the sibling package. Delete them during migration.

**Exception:** the shim at the MCP-tool/direct-Python boundary (where `mcp_coder` chooses whether to call `mcp_tools_py` via MCP protocol vs direct import) may still be worth keeping as a documented chokepoint. That's a call-surface concern, not a repo-boundary concern — unrelated to the mono-repo question.

---

## 6. Migration phases

Assumes Option B. Each phase is a set of PRs, not one PR.

### Phase M0 — Decision + skeleton

1. **Decide.** Mono-repo or stay multi-repo. If multi-repo, continue with `mcp_utils_plan.md`. This phase is the point of no return.
2. **Create `mcp-suite` repo.** Empty. Add workspace `pyproject.toml` (uv workspace), root tool configs (`.importlinter`, `tach.toml`, `pyproject.toml` with `[tool.black]` / `[tool.isort]` / `[tool.ruff]` / `[tool.mypy]` / `[tool.pytest.ini_options]`), CI skeleton, root `CLAUDE.md`.
3. **Import `docs/` from mcp_coder** as the canonical docs tree. Preserve git history via `git subtree` or `git filter-repo`.

### Phase M1 — Import the 5 codebases, preserving history

For each of `mcp_coder`, `mcp_tools_py`, `mcp_workspace`, `mcp_config` (and a fresh `mcp-utils` populated from the extraction plan's Phase 2 picks):

1. `git subtree add` or `git filter-repo --to-subdirectory-filter packages/<name>` to move the repo into `packages/<name>/` while keeping its history visible.
2. Per-package `pyproject.toml` keeps only: distribution metadata, runtime deps, entry points. All tool config deleted (inherited from root).
3. Confirm each package still builds standalone: `uv build packages/<name>`.
4. CI runs per-package tests. Everything green.

At this point the monorepo is a monorepo but has the **same content** as the 4 source repos glued together — no refactoring yet.

### Phase M2 — Collapse duplicates

Now the easy part: deduplicate the modules that motivated the extraction plan in the first place, but as **single PRs** instead of 5-PR coordinated dances.

1. `subprocess_runner`: merge the best-of-three into `packages/mcp-utils/src/mcp_utils/subprocess/runner.py`, delete the 3 copies in `mcp-coder` / `mcp-tools-py` / `mcp-config`, update imports. One PR.
2. `log_utils`: same pattern. One PR.
3. `file_utils` → `mcp_utils.fs.read_file`: same. One PR.
4. `path_utils` → `mcp_utils.fs.path_security`: same. One PR.

Each of these is what the multi-repo extraction plan calls a "module tracking issue" with a 5-checkbox PR sequence. In the monorepo each is a single PR touching multiple packages atomically.

### Phase M3 — Collapse cross-package moves

The extraction plan's phases 4 and 5:

1. **Formatters** (ex-phase 4): move `mcp_coder/formatters/` → `packages/mcp-tools-py/src/mcp_tools_py/formatter/`, update callers. Split `pyproject_config.py` as Phase 0 findings require. One PR.
2. **Git operations** (ex-phase 5a): move `mcp_coder/utils/git_operations/` → `packages/mcp-workspace/src/mcp_workspace/file_tools/git_operations/`. Expose as MCP tools. Update mcp_coder workflows to call via the (now in-process) sibling import. One PR.
3. **GitHub operations** (ex-phase 5b): move `mcp_coder/utils/github_operations/` → `packages/mcp-workspace/src/mcp_workspace/file_tools/github_operations/`. One PR.

In the multi-repo world these 3 moves are ~30 files across 2 repos each, with coordination issues. In the monorepo each is a single PR reviewed as a unit.

### Phase M4 — Tooling consolidation

1. Delete the duplicated `tools/format_all.sh`, `tools/lint_imports.sh`, `tools/tach_check.sh` from subpackages — replace with root-level scripts that operate workspace-wide.
2. Delete the duplicated `.claude/` directories from subpackages — single root `.claude/`.
3. Delete the duplicated `docs/repository-setup/` directories — single root copy, updated per §4 above.
4. Delete the duplicated `.github/workflows/` — single root CI.
5. Delete the per-package shims in `mcp_coder` that exist only because of repo boundaries.

### Phase M5 — First unified release

1. Tag `v1.0.0` at the workspace root.
2. `publish.yml` builds all 5 distributions and publishes to PyPI with version `1.0.0`.
3. Archive the 4 source repos on GitHub with a pinned README pointing at the new `mcp-suite` repo.
4. Update downstream users' `pip install` lines — they still install the same package names, just from the new source of truth.

### Phase M6 — Cleanup

1. Close any stale tracking issues from the extraction plan.
2. Update `docs/architecture/architecture.md` to describe the workspace layout instead of the 4-repo diagram.
3. Delete `mcp_utils_plan.md` and `mcp_monorepo_plan.md` — both served their purpose; the code now speaks for itself.

---

## 7. Comparison matrix — mono-repo vs multi-repo extraction

| Dimension | Multi-repo + mcp-utils (current plan) | Mono-repo (this plan) |
|---|---|---|
| Release coupling | 5 repos, N PRs per module dedupe | 1 repo, 1 PR per dedupe |
| Atomic cross-package refactor | Not possible (no cross-repo PR) | Native |
| Per-module extraction ceremony | Tracking issue + 5-PR checklist + manual grep | Single PR |
| Tool config duplication | 4× `.importlinter`, 4× `tach.toml`, 4× pyproject tool tables | 1× each at root |
| Layer enforcement across packages | Reviewer memory only (no mechanism spans repos) | Single import-linter/tach config enforces |
| Shim layer | Required (extraction plan rule) | Not required (delete the shims) |
| LLM context for cross-package work | Reference-project lookups, CLAUDE.md "Shared libraries" block | Direct file reads |
| MCP server install footprint | Separate dist per server — minimal | Separate dist per server — minimal (unchanged, because Option B) |
| CLI entry points (`mcp-coder`, `mcp-config`, `icoder`) | Per-repo scripts | Per-package scripts (unchanged) |
| `.mcp.json` invocation model | Unchanged | Unchanged |
| Independent version bumps per package | Possible | Not possible (locked-version model) |
| Independent repo lifecycle (fork, archive, transfer) | Possible | Not possible (all-or-nothing) |
| Downstream `pip install X` | Unchanged | Unchanged |
| CI pipeline complexity | 4 separate pipelines | 1 pipeline with package matrix |
| `docs/repository-setup/` template maintenance | 1 source of truth, manually referenced | 1 source of truth that *is* the live config (no drift) |
| Migration effort | Already mostly planned (§0–§7 of mcp_utils_plan) | Larger upfront cost (Phases M0–M6), smaller ongoing cost |

---

## 8. Open questions for this plan

1. **Workspace tool choice.** uv (fast, modern, workspace-native since 0.4), hatch (mature workspaces), or poetry (biggest ecosystem, heavier)? I'd default to **uv**: it's already the direction of travel, and the existing `pyproject.toml` is setuptools-scm based which uv handles.
2. **History preservation strategy.** `git subtree add` keeps history but clutters the log. `git filter-repo --to-subdirectory-filter` rewrites cleanly but needs 4 separate rewrites then merges. Choose based on how much history we care about.
3. **Repo name.** `mcp-suite`? `mcp-monorepo`? Something else? Needs bikeshedding.
4. **What to do with `mcp_config`.** The extraction plan marks it "exists, to be reviewed" in §0. If review concludes mcp_config should be deprecated or absorbed into mcp_coder, the monorepo migration is the right moment to do it — don't bring dead code along.
5. **icoder extraction.** Currently deferred in both plans (§7 of mcp_utils_plan, "out of scope"). Same answer in monorepo: leave inside `packages/mcp-coder/src/mcp_coder/icoder/` until it earns its own package.
6. **Jenkins.** Deferred in both plans. Same answer in monorepo: leave inside `packages/mcp-coder/src/mcp_coder/utils/jenkins_operations/` until (if) a `packages/mcp-jenkins/` is worth creating.
7. **Are there any current or planned users of individual repos who would object to consolidation?** If yes, that's the strongest argument against. If no (which is my current read), the multi-repo shape is accidental complexity.

---

## 9. Recommendation

If cross-repo ceremony is a significant pain — and the multi-repo extraction plan itself documents that it is (see its §Cross-cutting decisions still open, item 1, and its §"Planning and implementation process (cross-repo work)") — then **Option B mono-repo is the right answer**. It delivers everything the extraction plan wants (dedupe, clear layering, one source of truth for shared code) while *eliminating* the shim layer, the per-module 5-PR dance, the reference-project indirection for LLM context, and the 4× tooling drift.

If the 4 repos genuinely need independent lifecycles — different release cadences, different owners, different audiences, or a plausible future where one is forked/archived independently — then **stay multi-repo and execute `mcp_utils_plan.md` as-is**. The extraction plan is solid; the only thing wrong with it is that the underlying repo split might itself be unnecessary.

The decision is binary and should be made **before** starting Phase 1 of the extraction plan. Starting extraction and then switching to mono-repo wastes the extraction work. Starting mono-repo and then switching back to extraction is also waste. Pick one.
