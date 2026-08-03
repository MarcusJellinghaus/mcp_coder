# Step 1 — Parse the rich `tools:` block (`skill_tools.py`) + `ClaudeSkill.tools_block`

**Read `pr_info/steps/summary.md` first.** This is the pure, dependency-free parser — the structural
half of the bridge. It records **raw strings only**; no `Matcher`/`PermissionFrame`, no token
semantics (those are Step 2). Parsing must be callable without `load_skills` (I5.1 reuse).

## WHERE
- **New:** `src/mcp_coder/icoder/permissions/skill_tools.py`
- **New tests:** `tests/icoder/test_permissions_skill_tools.py` (matching the existing
  `test_permissions_<module>.py` convention used for every other `permissions/` module)
- **Modified:** `src/mcp_coder/icoder/skills.py` (add field + populate it)
- **Modified:** `.importlinter` (add `skill_tools` to `permissions_leaf_isolation` source_modules,
  **and** add `mcp_coder.icoder.skills` + `mcp_coder.icoder.core` to that contract's `forbidden_modules`
  so the leaf's "imports nothing from skills/core" guarantee is actually enforced — see HOW)

## WHAT
```python
# skill_tools.py
from collections.abc import Mapping

@dataclass(frozen=True)
class SkillToolsBlock:
    base: str | None                       # "inherit" | "none" | None (bare-use block)
    allow: tuple[str, ...] = ()            # raw tokens, verbatim
    deny: tuple[str, ...] = ()             # raw tokens, verbatim (incl. @refs)
    use: str | None = None                 # block-level `use: name`, else None
    errors: tuple[str, ...] = ()           # fatal structural mistakes → skill blocked (Step 2/4)
    advisories: tuple[str, ...] = ()       # lint: non-mcp__ tokens in a rich block (for I5.1)

def parse_tools_block(meta: Mapping[str, object]) -> SkillToolsBlock | None: ...
```
`skills.py`: add `tools_block: SkillToolsBlock | None = None` to `ClaudeSkill`; in `load_skills`
set `tools_block=parse_tools_block(meta)`.

## HOW
- `skill_tools.py` imports **nothing** from the project (only `dataclasses`, `typing`/`collections.abc`).
  This keeps `permissions/` a leaf; `skills.py → permissions.skill_tools` is the only new edge (downward).
- Frontmatter key is `tools`. Read it with a **membership test** (`"tools" in meta`) plus
  `meta["tools"]`, never `meta.get("tools")` — the latter returns `None` for both an absent key and a
  present-but-null block, which are on opposite sides of the fail-open boundary (see ALGORITHM).
- `import`-linter: append `mcp_coder.icoder.permissions.skill_tools` to the `permissions_leaf_isolation`
  `source_modules` list, and append `mcp_coder.icoder.skills` and `mcp_coder.icoder.core` to that
  contract's `forbidden_modules` (which today lists only `icoder.ui`/`icoder.services`/`textual`/
  langchain). The existing pure source modules (`model`/`matcher`/`resolver`/`loader`) and the new
  `skill_tools` import none of `skills`/`core`, so the contract stays green while now *enforcing* the
  leaf's independence from `icoder.skills`/`icoder.core` — the guarantee the final AC relies on.

## ALGORITHM (`parse_tools_block`)
```
if "tools" not in meta: return None       # ABSENT — the ONLY fail-open case (key not present at all)
raw = meta["tools"]
# PRESENT-but-null (`tools:` written with no value → YAML parses it to None) is MALFORMED,
# NOT absent. `meta.get("tools")` returns None for BOTH, so the membership test above is
# load-bearing: it is the fail-open/fail-closed boundary the issue's AC calls out.
if raw is None or not isinstance(raw, Mapping) or not raw:   # null / list / scalar / empty mapping
    return SkillToolsBlock(base=None, errors=("tools: must be a non-empty mapping",))
# Initialise every local up front: the `use:`+inline path below records an error and falls
# through to the shared return, so nothing may be left unbound.
base: str | None = None; allow: list[str] = []; deny: list[str] = []
use_val: str | None = None; errors: list[str] = []
use = raw.get("use"); has_inline = any(k in raw for k in ("base","allow","deny"))
if use is not None and has_inline:
    use_val = str(use); errors.append("use: cannot combine with base/allow/deny")
elif use is not None: return SkillToolsBlock(base=None, use=str(use))   # bare use → valid; blocked in Step 2
else: validate base ∈ {"inherit","none"} (missing/invalid → err); allow/deny must be list[str]
      — on failure record the err and leave that list EMPTY; never carry a non-string item forward
# `allow`/`deny` now hold strings only, so `.startswith` is total (no AttributeError on the
# non-string-item case).
advisories = [t for t in allow+deny if not t.startswith(("mcp__","@"))]  # rich-block lint only
return SkillToolsBlock(base, tuple(allow), tuple(deny), use_val, tuple(errors), tuple(advisories))
```

## DATA
- **Absent** = the `tools` key is not in `meta` → `None`. **Present-but-null** (`tools:` with no
  value) is **malformed**, not absent — see the ALGORITHM note; this is the fail-open boundary.
- Malformed block → `SkillToolsBlock` with non-empty `errors` (and `base=None`).
- Valid rich block → `base` one of `"inherit"`/`"none"`, `allow`/`deny` verbatim tuples, `errors=()`.
- Bare-use block → `base=None, use="name", errors=()`.
- `advisories` lists non-`mcp__`/non-`@` tokens (e.g. `Bash(...)`, `gh`) for I5.1; never affects runtime.

## TESTS (write first)
Parametrise over the malformed set, each case spelled out so none can be collapsed away:
`{"tools": [...]}` (YAML list), **`{"tools": None}` (present-but-null — its own case, NOT the same
as the empty mapping)**, `{"tools": {}}` (empty mapping), `{"tools": "x"}` (scalar), missing `base`,
invalid `base` value (`"foo"`), scalar `allow`, non-string list item, `use:`+inline. Assert each
yields non-empty `errors` — in particular assert `{"tools": None}` returns a `SkillToolsBlock` with
errors and **not** `None`, since `meta.get("tools")` cannot distinguish it from an absent key.
Plus: **absent** `tools` key (`{}`) → `None`; valid `base: inherit`+`allow`/`deny` round-trips
verbatim; `base: none, allow: []` → valid empty; bare `use:` → `use` set, no `errors`; a rich block
with a `Bash(...)` token → recorded in `advisories`, not `errors`. Then a `load_skills` test proving
`ClaudeSkill.tools_block` is populated from a SKILL.md carrying a `tools:` block, and stays `None`
when the block is absent (and `allowed_tools` remains parsed as before).

## LLM PROMPT
> Implement Step 1 of `pr_info/steps/summary.md` (see `pr_info/steps/step_1.md`). Using TDD, first
> write `tests/icoder/test_permissions_skill_tools.py` covering the malformed-vs-absent parametrisation
> (including `{"tools": None}` — present-but-null — as a **malformed** case distinct from both an
> absent key and `{"tools": {}}`), the bare-`use:` case, and the `advisories` lint, plus a
> `load_skills` test asserting
> `ClaudeSkill.tools_block` is populated. Then create the pure `permissions/skill_tools.py`
> (`SkillToolsBlock` + `parse_tools_block`, imports nothing project-side), add the `tools_block`
> field to `ClaudeSkill` and populate it in `load_skills` (leaving `allowed_tools` untouched), and add
> `skill_tools` to the `permissions_leaf_isolation` contract in `.importlinter`. Run
> `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`,
> `mcp__tools-py__run_pytest_check` (`extra_args=["-n","auto","-m","not git_integration and not
> claude_cli_integration and not claude_api_integration and not formatter_integration and not
> github_integration and not langchain_integration"]`) and `mcp__tools-py__run_lint_imports_check`
> until all pass. One commit.
