# I2.4 (#1061) — Skill `tools:` block → `PermissionFrame` builder, transport + broken-skill feedback

## Goal

Deliver the single, canonical **`skill → PermissionFrame` bridge** for M2:

1. **Parse** a skill's rich `tools:` block (`base` / `allow` / `deny` / `use:`) — today only the flat
   legacy `allowed-tools` list is read.
2. **Build** a `PermissionFrame` from *any* skill (rich block *or* legacy list), realising design
   models **A** (`base: inherit` + `allow`), **B** (`+ deny`) and **C** (`base: none`).
3. **Carry** that frame to the enforcement gateway — replacing the interim raw-string carrier that
   I2.3 never swapped out.
4. **Tell the user** when a skill's declaration is broken (invocation refusal, startup listing,
   autocomplete marking) and when the permission config is degraded.

Frame *resolution* (models A/B/C → ALWAYS/NEVER) already ships and is verified — the resolver
(`permissions/resolver.py`) needs **no change** (issue decision D11). This work only *constructs* and
*transports* frames and *surfaces* failures.

## Architectural / design changes

| Area | Before | After |
|---|---|---|
| Skill tool declaration | only `allowed-tools` (flat list) parsed in `skills.py` | new pure parser `permissions/skill_tools.py` reads the rich `tools:` block into `SkillToolsBlock` (raw strings only); stored on `ClaudeSkill.tools_block`. `allowed_tools` untouched (Claude fidelity). |
| Frame construction | `build_legacy_frame` in `gateway.py` builds only the legacy model-C case from raw tokens | new pure builder `permissions/skill_frame.py::build_frame(...) -> SkillFrame` is the *one* place that maps any skill to a frame. `build_legacy_frame` is **deleted**; the gateway becomes enforcement-only. |
| Transport carrier | `SendToLLM.allowed_tools: tuple[str,...]` (raw strings) → service builds the frame per turn | `SendToLLM.skill_name: str \| None` carries provenance. Startup builds `{skill_name: SkillFrame}` **once**; `AppCore` owns the snapshot (design §8.1), looks it up per turn and calls `LLMService.stream(text, *, frame=...)`. `core/types.py` stays permission-free. |
| Enforcement flag | `enforce_skill_tools` is a `RealLLMService`/`FakeLLMService` constructor param | deleted from the services; becomes a module-level constant `ENFORCE_SKILL_TOOLS` in `cli/commands/icoder.py` (single `#1062` flip site, no CLI flag). |
| Warning emission | `RealLLMService.stream` emits `permission_warning` events | moves to `AppCore.stream_llm` (from `SkillFrame.warnings`); the service no longer knows about frame construction. |
| Blocked skills | a broken declaration silently yields a zero-tool turn | a broken skill is **blocked**: registered + visible, but refuses to run with a reason, marked in the `/` autocomplete, and listed at startup. |
| Degraded config | only a Textual-swallowed `logger.error` | a loud startup line. |
| `PermissionFrame.base` | bare `str` | `Base = Literal["inherit","none"]` alias (D15). |

### One deliberate deviation from the issue's decision table (needs no further approval unless you object)

The issue's **D12** says blocked-ness is decided *at parse time* from `SkillToolsBlock.errors` and set on
`Command.disabled_reason` inside `register_skill_commands`, with `SkillFrame` carrying no blocking flag.
Re-reading D7(b)/D8, two of the three blocking cases (`base: none` with *nothing surviving parse*, and
bare `use:`) are **only knowable at build time** — `parse_tools_block` imports nothing and cannot run
`parse_matcher`. Splitting the decision across parse + build is both more complex and a correctness trap.

**This plan decides blocked-ness in one place — `build_frame` — and carries it as
`SkillFrame.blocked_reason: str \| None`.** To keep D12's **provider-agnostic** reach, the
`{skill_name: SkillFrame}` map is built **unconditionally at startup for every provider** (`build_frame`
is pure and needs no `mcp_config`), so a malformed `tools:` block sets `Command.disabled_reason`
regardless of provider — exactly as D12's parse-time blocking did, and unlike a map gated behind
`provider=="langchain" and mcp_config` (which would leave langchain-without-`mcp_config` and
non-langchain skills silently unblocked). Only the gateway *enforcement* stays langchain-gated.
`Command.disabled_reason` remains the single generic signal the autocomplete and the `handle_input`
refusal read; it is simply populated once, at startup, from `build_frame`'s result instead of from
`register_skill_commands`.

**Scope limit on the provider-agnostic map (plan-review run 2).** Only `tools_block`-driven blocking
is provider-agnostic. The **legacy `allowed-tools` path** receives
`enforce_skill_tools=ENFORCE_SKILL_TOOLS if provider == "langchain" else False`, because
`allowed-tools` is Claude-provider-**native**: without the gate, #1062 flipping the constant would
block every shell-only skill under the claude provider too. See Step 3.

### Decision: the D8 two-empties predicate reads the *forced* base, with a cause-specific reason

`build_frame` evaluates D8's "declared but nothing survived" predicate against the **post-D3** base,
so a dropped `deny` entry that forces `base="none"` **can** block a skill whose `allow` also filtered
to empty. D7 wins over D3's "run + warn" here: never burn an LLM turn on a zero-tool skill.
**But the `blocked_reason` must name the real cause** — `two_empties` returns two distinct strings,
one for the plain empty-`allow` case and one naming the dropped `deny` entry. Reporting an empty
`allow` list when the block was actually triggered by an unresolvable `deny` token is a defect.

## Canonical `skill → frame` mapping (implemented by `build_frame`)

| Input | Result |
|---|---|
| Rich `tools:` block, valid | `PermissionFrame(base=<stated>, allow=<parsed>, deny=<parsed>)` (A/B/C emergent) |
| Rich block malformed (non-mapping, **present-but-null**, empty, missing/invalid `base`, scalar `allow`/`deny`, non-string item, `use:`+inline) | recorded in `errors` → **BLOCKED**; builder still returns a fail-closed `base="none"` frame (for I5.1); runtime never reaches it. *Absent = the `tools` key is missing entirely; a present-but-null `tools:` is malformed, so `parse_tools_block` must test key membership, not `meta.get`* |
| `base: none, allow: []` | valid zero-tool sandbox — **runs**, no warning |
| `base: none`, declared `allow` non-empty but nothing survived parse | **BLOCKED** (D8) |
| bare `tools: { use: name }` | **BLOCKED** (D7b — unexpandable until I4.1) |
| `base: inherit`, everything dropped | no-op frame (`allow=()`, `deny=()`), **runs** |
| any entry dropped from **`deny`** (`@ref` or unparseable) | **force `base="none"`** + prominent warning (fail-closed, D3) |
| arg-scoped token in `allow` (`mcp__s__t(a=v)`) | kept, elevates the whole tool, + `#1053` warning (D5.4) |
| `mcp__srv__*` wildcard | enforced (supersedes I1.1's "not enforced" warning) |
| non-`mcp__` token (`Bash(...)`, `gh`) | ignored — advisory in a rich block, silent in a legacy list (D5.2) |
| legacy `allowed-tools` only | `base = "none" if <enforce> else "inherit"`, `allow=<parsed>`, `deny=()` (D4); `<enforce>` is `ENFORCE_SKILL_TOOLS` on langchain, always `False` on other providers |
| both blocks present | rich wins; legacy kept for Claude/adapter; **silent** (D14) |
| neither block | `SkillFrame(frame=None)` — inherit-everything status quo |

## Files created / modified

**Created**
- `src/mcp_coder/icoder/permissions/skill_tools.py` — `SkillToolsBlock` + `parse_tools_block`
- `src/mcp_coder/icoder/permissions/skill_frame.py` — `SkillFrame` + `build_frame`
- `tests/icoder/test_skill_tools.py`
- `tests/icoder/test_skill_frame.py`

**Modified**
- `src/mcp_coder/icoder/permissions/model.py` — `Base` Literal; retype `PermissionFrame.base`
- `src/mcp_coder/icoder/permissions/gateway.py` — delete `build_legacy_frame`
- `src/mcp_coder/icoder/skills.py` — `ClaudeSkill.tools_block`; `skill_name` in handler; `disabled_reasons` param
- `src/mcp_coder/icoder/core/types.py` — `SendToLLM.skill_name`; `Command.disabled_reason`
- `src/mcp_coder/icoder/core/app_core.py` — frame-map snapshot; `stream_llm`; blocked refusal; startup properties
- `src/mcp_coder/icoder/core/command_registry.py` — `get(name)` accessor
- `src/mcp_coder/icoder/services/llm_service.py` — `stream(*, frame=...)`; drop `enforce_skill_tools`; `Fake.last_frame`
- `src/mcp_coder/icoder/ui/app.py` — worker threads `skill_name`; startup notices
- `src/mcp_coder/icoder/ui/runtime_banner.py` — startup permission-notices helper
- `src/mcp_coder/icoder/ui/widgets/command_autocomplete.py` — mark disabled commands in the label (row stays selectable)
- `src/mcp_coder/cli/commands/icoder.py` — `ENFORCE_SKILL_TOOLS`; build frame map (all providers, langchain-only enforcement); pass to `AppCore`
- `src/mcp_coder/llm/types.py` — document `permission_warning` StreamEvent
- `.importlinter` — `skill_tools`/`skill_frame` join `permissions_leaf_isolation`; one `cli → skill_frame` ignore
- Tests migrated: `test_types`, `test_skills`, `test_app_core`, `test_app_pilot`, `test_llm_service`,
  `test_permissions_gateway`, `test_cli_icoder`, `test_command_registry`, `test_banner`,
  `test_command_autocomplete`

## Steps (one commit each, TDD)

1. **Parse** — `SkillToolsBlock` + `parse_tools_block`; store `ClaudeSkill.tools_block`.
2. **Build** — `Base` Literal; `SkillFrame` + `build_frame` (the full mapping table).
3. **Transport** — carrier swap `allowed_tools → skill_name`; frame-map snapshot in `AppCore`;
   `stream(*, frame=...)`; delete `build_legacy_frame`; warnings via `AppCore`; docstring.
4. **Blocked-skill handling** — `Command.disabled_reason`; invocation refusal; autocomplete marking.
5. **Startup feedback** — list broken skills by name + a loud degraded-config line.

Each step: write tests first, implement, then run pylint + pytest (`-n auto`, unit-only exclusions) +
mypy(strict) + `lint-imports` until green. `permission_warning` is undocumented today — Step 3 adds it.
