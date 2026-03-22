# labels.json Schema Reference

## Top-level Structure

```json
{
  "workflow_labels": [ ... ],
  "ignore_labels": ["label_name", ...]
}
```

## Per-label Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `internal_id` | string | yes | Short identifier used in code |
| `name` | string | yes | GitHub label name (e.g. `status-01:created`) |
| `color` | string | yes | Hex color without `#` |
| `description` | string | yes | Human-readable description |
| `category` | string | yes | One of: `human_action`, `bot_pickup`, `bot_busy` |
| `stale_timeout_minutes` | int | no | Timeout for `bot_busy` labels |
| `vscodeclaude` | object | no | Present only on `human_action` labels |

## `vscodeclaude` Block

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `emoji` | string | yes | Display emoji for the stage |
| `display_name` | string | yes | Human-readable stage name |
| `stage_short` | string | yes | Short stage key |
| `commands` | list[str] | no | Slash commands to run in order. Absent = display-only (no session). |

### `commands` field behavior

- **Absent** — label is display-only, no VSCode Claude session is started (e.g. `pr-created`).
- **1 command** — single-command flow: `["commands": ["/implementation_review_supervisor"]]`
- **2 commands** — initial + followup flow: `["commands": ["/issue_analyse", "/discuss"]]`

### Example

```json
{
  "internal_id": "created",
  "name": "status-01:created",
  "color": "10b981",
  "description": "Fresh issue, may need refinement",
  "category": "human_action",
  "vscodeclaude": {
    "emoji": "📝",
    "display_name": "ISSUE ANALYSIS",
    "stage_short": "new",
    "commands": ["/issue_analyse", "/discuss"]
  }
}
```
