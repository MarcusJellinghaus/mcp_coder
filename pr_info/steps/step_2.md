# Step 2: Skill Models and Loader — ClaudeSkill, ICoderSkillCommand, load_skills()

**Context**: See `pr_info/steps/summary.md` for full issue context. Step 1 must be complete.

## Goal

Create the skill data models and the loader that discovers and parses `.claude/skills/*/SKILL.md` files. No registration logic yet — just parsing.

## Prompt

```
Implement Step 2 of issue #720 (see pr_info/steps/summary.md for context).
Step 1 (Response.llm_text, Command.show_in_help, add_command) is complete.

Create src/mcp_coder/icoder/skills.py with:
1. ClaudeSkill dataclass — all frontmatter attributes + prompt_template body
2. ICoderSkillCommand dataclass — thin wrapper with skill ref + command_name
3. load_skills(project_dir) — discover, parse, filter
4. Write tests first (TDD), then implement.
5. Add python-frontmatter to pyproject.toml dependencies.
6. Run all three code quality checks after changes.
```

## Tests First — `tests/icoder/test_skills.py`

### WHERE
`tests/icoder/test_skills.py` — new file

### WHAT — test functions using `tmp_path` fixtures

```python
def test_load_skills_discovers_valid_skill(tmp_path: Path) -> None:
    """load_skills finds and parses a valid SKILL.md."""

def test_load_skills_parses_all_frontmatter_fields(tmp_path: Path) -> None:
    """All frontmatter attributes are parsed into ClaudeSkill fields."""

def test_load_skills_defaults_for_missing_optional_fields(tmp_path: Path) -> None:
    """Missing optional fields get sensible defaults."""

def test_load_skills_filters_user_invocable_false(tmp_path: Path) -> None:
    """Skills with user-invocable: false are excluded."""

@pytest.mark.parametrize("scenario", ["empty_dir", "no_skill_md", "malformed_file"])
def test_load_skills_skip_cases(tmp_path: Path, scenario: str) -> None:
    """load_skills handles edge cases: empty dir, missing SKILL.md, malformed files."""

def test_load_skills_multiple_skills(tmp_path: Path) -> None:
    """Multiple valid skills are all returned."""

def test_icoder_skill_command_creation() -> None:
    """ICoderSkillCommand wraps a ClaudeSkill with command_name."""

def test_claude_skill_name_from_directory(tmp_path: Path) -> None:
    """ClaudeSkill.name is derived from the directory name."""
```

### HOW — fixture helper
```python
def _create_skill(tmp_path: Path, skill_name: str, frontmatter: str, body: str) -> Path:
    """Helper to create a .claude/skills/<name>/SKILL.md file."""
    skill_dir = tmp_path / ".claude" / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}---\n\n{body}")
    return skill_dir
```

## Implementation — `src/mcp_coder/icoder/skills.py`

### WHERE
`src/mcp_coder/icoder/skills.py` — new file

### WHAT — data models

```python
@dataclass(frozen=True)
class ClaudeSkill:
    """Full Claude Code skill spec parsed from SKILL.md."""
    name: str                           # directory name (e.g. "issue_analyse")
    description: str                    # frontmatter 'description'
    prompt_template: str                # markdown body
    argument_hint: str | None = None    # frontmatter 'argument-hint'
    disable_model_invocation: bool = False
    user_invocable: bool = True
    allowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    effort: str | None = None
    context: str | None = None
    agent: str | None = None
    hooks: dict[str, object] | None = None
    paths: list[str] | None = None
    shell: str | None = None
```

```python
@dataclass(frozen=True)
class ICoderSkillCommand:
    """Thin wrapper for iCoder runtime. Holds skill + command name."""
    skill: ClaudeSkill
    command_name: str  # e.g. "/issue_analyse"
```

### WHAT — loader function

```python
def load_skills(project_dir: Path) -> list[ClaudeSkill]:
    """Discover and parse skills from <project_dir>/.claude/skills/*/SKILL.md."""
```

### ALGORITHM — load_skills pseudocode
```
skills_dir = project_dir / ".claude" / "skills"
if not skills_dir.is_dir(): return []
for each subdirectory in skills_dir:
    try to parse subdirectory/SKILL.md with python-frontmatter
    if parse fails: log warning, skip
    build ClaudeSkill from frontmatter metadata + content body
    if user_invocable is False: skip
    append to results
return results
```

### NOTES
- **Import**: `import frontmatter` (the pip package is `python-frontmatter` but imports as `frontmatter`)
- **Error handling**: Catch `Exception` broadly in the try/except around each SKILL.md parse, since `frontmatter` can raise various error types on malformed input (YAML errors, encoding errors, etc.)

### DATA — return value
`list[ClaudeSkill]` — only skills with `user_invocable != False`

## Dependency — `pyproject.toml`

### WHERE
`pyproject.toml` line 37 (before closing `]` of dependencies)

### WHAT
Add `"python-frontmatter>=1.0.0",` to the `dependencies` list.

## Commit Message
```
feat(icoder): add ClaudeSkill model and skill loader
```
