"""On-disk ``@group`` expansion tests for ``load_permission_config`` (I4.1).

Cross-layer expansion, provenance, declaration order and fail-closed
granularity all need real layer files, so they live here rather than in the
pure expander tests. Every fail-closed assertion is on ``config.rules``: a
degraded config short-circuits ``resolve()``, which would pass vacuously.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_coder.icoder.permissions.loader import load_permission_config
from mcp_coder.icoder.permissions.model import Layer, Policy
from mcp_coder.icoder.permissions.resolver import resolve


class _Layers:
    """Writes the three ``.icoder`` layer files under a temp root."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.user_root = tmp_path / "user"
        self.user_root.mkdir()
        monkeypatch.setattr(
            "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
            lambda _app: self.user_root,
        )
        self.project_dir = tmp_path / "project"
        self.project_dir.mkdir()

    def write(self, layer: str, body: dict[str, object]) -> Path:
        """Write ``body`` to ``layer``'s settings file; return its absolute path."""
        root = self.user_root if layer == "user" else self.project_dir
        name = "settings.local.json" if layer == "local" else "settings.json"
        icoder = root / ".icoder"
        icoder.mkdir(exist_ok=True)
        path = icoder / name
        path.write_text(json.dumps(body), encoding="utf-8")
        return path.resolve()


@pytest.fixture
def layers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Layers:
    return _Layers(tmp_path, monkeypatch)


def test_ref_resolves_against_merged_group_map(layers: _Layers) -> None:
    """A group defined in ``user`` resolves from a ``project`` rule."""
    layers.write("user", {"toolGroups": {"git": ["mcp__git__status"]}})
    layers.write("project", {"allow": ["@git"]})

    config = load_permission_config(layers.project_dir)

    assert config.degraded is False
    assert [(r.matcher.tool, r.layer) for r in config.rules] == [("status", "project")]


def test_transitive_ref_across_layers(layers: _Layers) -> None:
    """A ``user`` group member referencing a ``project`` group resolves."""
    layers.write("user", {"toolGroups": {"write": ["@read", "mcp__gh__push"]}})
    layers.write(
        "project",
        {"toolGroups": {"read": ["mcp__gh__view"]}, "allow": ["@write"]},
    )

    config = load_permission_config(layers.project_dir)

    assert config.degraded is False
    assert [r.matcher.tool for r in config.rules] == ["view", "push"]
    assert [m.tool for m in config.groups["write"]] == ["view", "push"]


def test_group_rule_provenance(layers: _Layers) -> None:
    """``matched_rule`` is the origin rule carrying the authored ref and path."""
    path = layers.write(
        "project",
        {"toolGroups": {"git": ["mcp__git__status"]}, "allow": ["@git"]},
    )

    config = load_permission_config(layers.project_dir)
    decision = resolve("mcp__git__status", None, None, config)

    assert decision.policy is Policy.ALWAYS
    assert decision.source == Layer("project")
    assert decision.matched_rule is not None
    assert decision.matched_rule.ref == "@git"
    assert decision.matched_rule.matcher is None
    assert decision.matched_rule.source_path == path
    assert decision.matched_rule.layer == "project"


def test_origin_rule_is_never_a_member(layers: _Layers) -> None:
    """No member of ``config.rules`` is an origin rule (D13)."""
    layers.write(
        "project",
        {
            "toolGroups": {"git": ["mcp__git__status", "mcp__git__log"]},
            "allow": ["@git", "mcp__fs__read"],
        },
    )

    config = load_permission_config(layers.project_dir)

    assert len(config.rules) == 3
    assert all(r.ref is None and r.matcher is not None for r in config.rules)


def test_specific_direct_rule_beats_broad_group(layers: _Layers) -> None:
    """A direct ``allow`` on a member beats a broad ``@git`` ``ask``."""
    layers.write(
        "project",
        {
            "toolGroups": {"git": ["mcp__git__*"]},
            "ask": ["@git"],
            "allow": ["mcp__git__log"],
        },
    )

    config = load_permission_config(layers.project_dir)

    assert resolve("mcp__git__log", None, None, config).policy is Policy.ALWAYS
    assert (
        resolve("mcp__git__status", None, None, config).policy is Policy.AFTER_APPROVAL
    )


def test_earlier_authored_group_wins(layers: _Layers) -> None:
    """Two groups sharing a member, same policy/layer: the earlier ref wins."""
    layers.write(
        "project",
        {
            "toolGroups": {"a": ["mcp__git__log"], "b": ["mcp__git__log"]},
            "allow": ["@b", "@a"],
        },
    )

    config = load_permission_config(layers.project_dir)
    decision = resolve("mcp__git__log", None, None, config)

    assert decision.matched_rule is not None
    assert decision.matched_rule.ref == "@b"


def test_expansion_keeps_declaration_position(layers: _Layers) -> None:
    """Members land at the authored rule's position; later rules keep order."""
    layers.write(
        "project",
        {
            "toolGroups": {"git": ["mcp__git__status", "mcp__git__log"]},
            "allow": ["mcp__fs__read", "@git", "mcp__fs__write"],
        },
    )

    config = load_permission_config(layers.project_dir)

    assert [r.matcher.tool for r in config.rules] == [
        "read",
        "status",
        "log",
        "write",
    ]


def test_value_set_expands_to_n_rules(layers: _Layers) -> None:
    """A value-set matcher expands to N rules at load."""
    layers.write("project", {"allow": ["mcp__fs__write(path={a,b,c})"]})

    config = load_permission_config(layers.project_dir)

    assert len(config.rules) == 3
    assert {r.matcher.arg.value for r in config.rules if r.matcher.arg} == {
        "a",
        "b",
        "c",
    }


def test_direct_rule_provenance_absolute_and_layer_tag(layers: _Layers) -> None:
    """A direct rule carries the absolute source path and the layer tag."""
    path = layers.write("local", {"allow": ["mcp__fs__read"]})

    config = load_permission_config(layers.project_dir)

    assert len(config.rules) == 1
    rule = config.rules[0]
    assert rule.source_path == path
    assert rule.source_path is not None and rule.source_path.is_absolute()
    assert rule.layer == "local"
    assert rule.matcher.origin is None


def test_reload_follows_group_membership(layers: _Layers) -> None:
    """Editing only the group definition changes the resolved policy (D2)."""
    layers.write("user", {"toolGroups": {"git": ["mcp__git__status"]}})
    layers.write("project", {"defaultMode": "allow", "ask": ["@git"]})

    before = load_permission_config(layers.project_dir)
    assert resolve("mcp__git__log", None, None, before).policy is Policy.ALWAYS

    layers.write("user", {"toolGroups": {"git": ["mcp__git__log"]}})
    after = load_permission_config(layers.project_dir)

    assert resolve("mcp__git__log", None, None, after).policy is Policy.AFTER_APPROVAL


def test_unknown_ref_fails_closed(layers: _Layers) -> None:
    """An unknown ref degrades and its rule contributes nothing."""
    path = layers.write("project", {"allow": ["@missing"]})

    config = load_permission_config(layers.project_dir)

    assert config.degraded is True
    assert config.rules == ()
    joined = " ".join(config.errors)
    assert "@missing" in joined
    assert str(path) in joined


def test_ref_failure_spares_sibling_rules(layers: _Layers) -> None:
    """A bad ``@ref`` kills only its own rule (D11)."""
    layers.write("project", {"allow": ["@missing", "mcp__fs__read"]})

    config = load_permission_config(layers.project_dir)

    assert config.degraded is True
    assert [r.matcher.tool for r in config.rules] == ["read"]


def test_structural_failure_discards_whole_layer(layers: _Layers) -> None:
    """A malformed ``mcp__…`` token still discards its layer, siblings included."""
    layers.write("user", {"toolGroups": {"git": ["mcp__git__status"]}})
    layers.write("project", {"allow": ["@git", "mcp__fs__read", "github:*"]})

    config = load_permission_config(layers.project_dir)

    assert config.degraded is True
    assert config.rules == ()


def test_cycle_on_disk_terminates_and_degrades(layers: _Layers) -> None:
    """``@a -> @b -> @a`` terminates, degrades and contributes no rules."""
    layers.write(
        "project",
        {"toolGroups": {"a": ["@b"], "b": ["@a"]}, "allow": ["@a"]},
    )

    config = load_permission_config(layers.project_dir)

    assert config.degraded is True
    assert config.rules == ()


def test_unreferenced_broken_group_fails_wholesale_without_degrading(
    layers: _Layers,
) -> None:
    """A broken group nobody references is stored empty; config stays healthy."""
    layers.write(
        "project",
        {"toolGroups": {"broken": ["mcp__git__status", "@missing"]}},
    )

    config = load_permission_config(layers.project_dir)

    assert config.degraded is False
    assert config.errors == ()
    assert config.groups["broken"] == ()


def test_scenario_member_group_ref_resolves(layers: _Layers) -> None:
    """A ``@git`` scenario member expands against the group map."""
    layers.write(
        "project",
        {
            "toolGroups": {"git": ["mcp__git__status", "mcp__git__log"]},
            "toolScenarios": {
                "review": {"base": "inherit", "allow": ["@git", "mcp__gh__view"]}
            },
        },
    )

    config = load_permission_config(layers.project_dir)

    assert config.degraded is False
    block = config.scenarios["review"]
    assert block.base == "inherit"
    assert [m.tool for m in block.allow] == ["status", "log", "view"]
    assert block.deny == ()
    assert block.errors == ()


def test_scenario_resolves_group_from_another_layer(layers: _Layers) -> None:
    """A scenario in ``project`` resolves a group defined in ``user``."""
    layers.write("user", {"toolGroups": {"git": ["mcp__git__status"]}})
    layers.write(
        "project",
        {"toolScenarios": {"review": {"base": "none", "deny": ["@git"]}}},
    )

    config = load_permission_config(layers.project_dir)

    block = config.scenarios["review"]
    assert block.base == "none"
    assert [m.tool for m in block.deny] == ["status"]
    assert block.errors == ()


def test_scenario_unknown_allow_ref_fails_side_wholesale(layers: _Layers) -> None:
    """An unknown ``allow`` ref empties that side and is recorded, not degraded."""
    layers.write(
        "project",
        {
            "toolScenarios": {
                "review": {"base": "inherit", "allow": ["mcp__gh__view", "@nope"]}
            }
        },
    )

    config = load_permission_config(layers.project_dir)

    assert config.degraded is False
    assert config.errors == ()
    block = config.scenarios["review"]
    assert block.allow == ()
    assert block.base == "inherit"
    joined = " ".join(block.errors)
    assert "review" in joined
    assert "@nope" in joined


def test_scenario_failed_deny_forces_base_none(layers: _Layers) -> None:
    """A failed ``deny`` side fails closed: ``base`` becomes ``none``."""
    layers.write(
        "project",
        {"toolScenarios": {"review": {"base": "inherit", "deny": ["@nope"]}}},
    )

    config = load_permission_config(layers.project_dir)

    assert config.degraded is False
    block = config.scenarios["review"]
    assert block.deny == ()
    assert block.base == "none"
    assert block.errors
