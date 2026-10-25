"""Consistency checks between labels.json and the HTML workflow matrix."""

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LABELS_JSON = REPO_ROOT / "src" / "mcp_coder" / "config" / "labels.json"
MATRIX_HTML = (
    REPO_ROOT / "docs" / "processes-prompts" / "github_Issue_Workflow_Matrix.html"
)
LABEL_NAME_RE = re.compile(r'class="label-name">([^<]+)<')
AUTO_COMMAND_RE = re.compile(r'class="auto-command">(.*?)</div>', re.DOTALL)


def _labels() -> list[dict[str, Any]]:
    data = json.loads(LABELS_JSON.read_text(encoding="utf-8"))
    labels: list[dict[str, Any]] = data["workflow_labels"]
    return labels


def _html() -> str:
    return MATRIX_HTML.read_text(encoding="utf-8")


def _cards() -> dict[str, str]:
    """Map label name -> card HTML block."""
    cards: dict[str, str] = {}
    for block in _html().split('class="label-card')[1:]:
        match = LABEL_NAME_RE.search(block)
        if match:
            cards[match.group(1).strip()] = block
    return cards


def test_every_label_has_a_card() -> None:
    names = set(LABEL_NAME_RE.findall(_html()))
    missing = sorted({label["name"] for label in _labels()} - names)
    assert not missing, f"labels without a card: {missing}"


def test_every_card_label_exists_in_labels_json() -> None:
    names = set(LABEL_NAME_RE.findall(_html()))
    unknown = sorted(names - {label["name"] for label in _labels()})
    assert not unknown, f"cards for unknown labels: {unknown}"


def test_vscodeclaude_commands_on_card() -> None:
    cards = _cards()
    for label in _labels():
        commands = label.get("vscodeclaude", {}).get("commands")
        if not commands:
            continue
        match = AUTO_COMMAND_RE.search(cards.get(label["name"], ""))
        auto_line = match.group(1) if match else ""
        for cmd in commands:
            assert f"<code>{cmd}</code>" in auto_line, (label["name"], cmd)


def test_label_names_are_unique() -> None:
    names = LABEL_NAME_RE.findall(_html())
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert not duplicates, f"duplicate cards: {duplicates}"
