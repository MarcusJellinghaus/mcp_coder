# Architecture Documentation Maintenance

## Overview

**Purpose**: Maintain comprehensive Arc42 architecture documentation that enables LLM navigation and understanding of the mcp_coder system.

**Key Job**: When code changes occur, analyze impact on architecture and update documentation accordingly. Ensure documentation stays synchronized with codebase.

**How to Use**: This document provides detailed instructions for maintaining architecture documentation. Read the specific sections below for step-by-step guidance on what to document and how.

---

## 1. What to Document - Core Requirements

### 1.1 Arc42 Structure Requirements
**Process**: Maintain Arc42 sections to reflect current system architecture
**Reference**: Arc42 template methodology (https://arc42.org)

**Maintenance Steps**:
1. **Review Coverage**: Ensure all implemented Arc42 sections remain current
2. **Validate Content**: Check each section against actual system state
3. **Update Dependencies**: Sync constraints and requirements across files
4. **Cross-Reference**: Verify consistency between main doc and related files

**Key Arc42 Sections to Maintain**:
- **Section 2**: Architecture constraints and dependencies
- **Section 3**: System context and component boundaries  
- **Section 4**: Solution strategy and component responsibilities
- **Section 5**: Building blocks and file navigation
- **Section 6**: Runtime scenarios and workflows
- **Section 8**: Cross-cutting concepts and patterns

**Source Files for Validation**:
- Main documentation: `docs/architecture/ARCHITECTURE.md`
- Project constraints: `.claude/CLAUDE.md`
- Testing configuration: `pyproject.toml`

### 1.2 Component Navigation for LLM
**Process**: Maintain accurate file/folder navigation paths for LLM code location

**Maintenance Steps**:
1. **Scan Codebase**: List all files in `src/mcp_coder/` directory structure
2. **Verify Paths**: Check all documented paths exist and are correct
3. **Update Descriptions**: Ensure component descriptions match actual functionality
4. **Apply Pattern**: Use consistent `Component: path/file.py - Description` format
5. **Test Navigation**: Validate LLM can locate components from documentation

**Documentation Location**:
- Building blocks: `docs/architecture/ARCHITECTURE.md` Section 5
- Key files appendix: `docs/architecture/ARCHITECTURE.md` Appendix

**Validation Source**:
- File structure: `src/mcp_coder/` directory tree

### 1.3 Testing Strategy Documentation
**Process**: Ensure testing markers and strategy remain synchronized across configuration files

**Maintenance Steps**:
1. **Compare Sources**: Check consistency between `pyproject.toml` markers, `.claude/CLAUDE.md` examples, and `ARCHITECTURE.md` Section 8
2. **Validate Markers**: Ensure all markers in `pyproject.toml` are documented with purpose and requirements
3. **Update Execution Patterns**: Verify recommended test execution commands match current marker structure
4. **Sync Documentation**: Update `ARCHITECTURE.md` Section 8 to reflect any marker changes

**Key Files to Monitor**:
- `pyproject.toml` - Source of truth for marker definitions
- `.claude/CLAUDE.md` - Execution examples and requirements
- `ARCHITECTURE.md` Section 8 - Architectural documentation of testing strategy

---

## 2. What to Document - Change Tracking

### 2.1 Dependency Changes
**Process**: Monitor and document dependency changes across configuration files

**Maintenance Steps**:
1. **Monitor Changes**: Watch for dependency modifications in `pyproject.toml`
2. **Check Constraints**: Verify changes align with documented architecture constraints
3. **Update Documentation**: Sync dependency changes to `ARCHITECTURE.md` Section 2
4. **Validate Requirements**: Ensure installation requirements stay current

**Change Triggers**:
- Adding new MCP servers
- Changing Python version requirements
- Adding external integrations
- Modifying testing dependencies

**Files to Synchronize**:
- `pyproject.toml` - Source of truth for dependencies
- `.claude/CLAUDE.md` - MCP server requirements
- `README.md` - Installation and setup requirements
- `ARCHITECTURE.md` Section 2 - Documented constraints

---

## 3. What to Document - System Changes

### 3.1 Component Relationship Updates
**Trigger Events**:
- New modules added to `src/mcp_coder/`
- Interface changes between components
- New CLI commands in `cli/commands/`
- Changes to MCP server usage

**Documentation Locations**:
- Component responsibilities: `ARCHITECTURE.md` Section 4
- File navigation: `ARCHITECTURE.md` Section 5  
- Runtime flows: `ARCHITECTURE.md` Section 6

### 3.2 Configuration Pattern Changes
**Sources to Monitor**:
- User configuration: `utils/user_config.py`
- Project configuration: `.claude/CLAUDE.md`
- Tool configuration: `pyproject.toml`
- Logging configuration: `utils/log_utils.py`

**Document Changes To**:
- Configuration management: `ARCHITECTURE.md` Section 8
- Cross-cutting concepts: `ARCHITECTURE.md` Section 8

---

## 4. How to Update - LLM Code Review Process

### Meta-Prompt for Fresh Sessions
**Copy-paste this to start architecture maintenance with no prior context:**

```bash
mcp-coder prompt "Architecture maintenance workflow:

1. READ PROCESS GUIDE:
   - Read docs/architecture/ARCHITECTURE_MAINTENANCE.md completely
   - Understand the 4-step maintenance process in Section 4
   - Note the quality gates in Section 5

2. EXECUTE SECTION 4.1 (Pre-Update Analysis):
   - Follow the process exactly as documented in the maintenance guide
   - Adapt the analysis for a fresh session (no prior context)
   - Use --store-response to save analysis results

3. NEXT STEPS:
   - Once Section 4.1 complete, proceed to Section 4.2
   - Continue through all sections (4.1 → 4.2 → 4.3 → 4.4)
   - Apply quality gates from Section 5

Begin with Section 4.1 now." --store-response
```

### 4.1 Pre-Update Analysis
**Step 1: Identify Changes**
```bash
mcp-coder prompt "Analyze recent code changes and identify architectural impacts:

1. CHANGE ANALYSIS:
   - List all modified files in src/mcp_coder/
   - Identify new dependencies in pyproject.toml
   - Check for new CLI commands in cli/commands/
   - Review changes to .claude/CLAUDE.md

2. ARCHITECTURAL IMPACT:
   - Which Arc42 sections need updates?
   - Are component relationships affected?
   - Do file/folder paths for LLM navigation need updates?
   - Are new testing markers needed?

3. DOCUMENTATION GAPS:
   - What's missing from current ARCHITECTURE.md?
   - Which cross-cutting concepts changed?

Provide specific file paths and section numbers for updates needed." --store-response
```

### 4.2 Documentation Update Process
**Step 2: Update Architecture Document**
```bash
mcp-coder prompt "Update docs/architecture/ARCHITECTURE.md based on analysis:

1. READ CURRENT DOCUMENTATION:
   - Read docs/architecture/ARCHITECTURE.md completely
   - Note current version and last updated date
   - Identify sections needing updates

2. UPDATE SPECIFIC SECTIONS:
   - Section 2 (Constraints): Update dependencies if changed
   - Section 3 (Context): Update component diagram if needed
   - Section 4 (Strategy): Update component responsibilities
   - Section 5 (Building Blocks): Update file/folder navigation paths
   - Section 6 (Runtime): Update workflow scenarios if changed
   - Section 8 (Cross-cutting): Update testing/config/quality patterns

3. UPDATE METADATA:
   - Increment version number
   - Update 'Last Updated' date
   - Add summary of changes to document

4. VALIDATE COMPLETENESS:
   - All new files/folders documented
   - Component relationships current
   - Testing strategy reflects pyproject.toml
   - File paths accurate for LLM navigation

5. BE SELECTIVE AND PRECISE:
   - Only update sections with actual changes
   - Do not add content just to show activity
   - If no changes needed, state "No updates required"
   - Focus on accuracy over completeness

Provide only the updated ARCHITECTURE.md sections that actually changed." --continue
```

### 4.3 Decision Documentation
**Step 3: Document Significant Decisions**
```bash
mcp-coder prompt "Document any significant architectural decisions made:

1. DECISION IDENTIFICATION:
   - Review changes for architectural decisions
   - Check if technology choices were made
   - Identify design pattern changes
   - Note dependency addition/removal decisions

2. DOCUMENT DECISIONS:
   - Add rationale to relevant ARCHITECTURE.md sections
   - Include context for design choices
   - Document why alternatives were rejected

3. DOCUMENT IN ARCHITECTURE.MD:
   - Add rationale to relevant sections if significant decisions were made
   - Update architecture document only, not maintenance document

Provide decision documentation for docs/architecture/ARCHITECTURE.md" --continue
```

### 4.4 Validation and Finalization
**Step 4: Comprehensive Review**
```bash
mcp-coder prompt "Perform final validation of architecture documentation:

1. DOCUMENTATION COMPLETENESS CHECK:
   - ✅ All new components documented in Building Blocks
   - ✅ File paths accurate for LLM navigation
   - ✅ Component responsibilities updated
   - ✅ Testing strategy reflects current markers
   - ✅ Cross-cutting concepts current

2. CONSISTENCY VALIDATION:
   - Compare ARCHITECTURE.md with actual codebase
   - Verify file paths exist and are correct
   - Check component descriptions match implementation
   - Validate testing markers match pyproject.toml

3. LLM NAVIGATION TEST:
   - Can LLM find files for any component?
   - Are component responsibilities clear?
   - Is testing strategy actionable?
   - Are configuration patterns documented?

4. FINAL VALIDATION:
   - Confirm all documentation is current and LLM-navigable
   - Verify file paths are accurate
   - Ensure component descriptions match reality

State completion status: "Architecture documentation validated" or list remaining issues." --continue
```

---

## 5. Quality Gates for Architecture Updates

### 5.1 Mandatory Verification Checklist
Before considering architecture documentation complete:

**Core Documentation**:
- [ ] **ARCHITECTURE.md Section 5**: All new files/folders documented with correct paths
- [ ] **Component responsibilities**: Clear ownership and interaction patterns
- [ ] **Testing strategy**: Reflects current pyproject.toml markers
- [ ] **File navigation**: LLM can locate any component from description

**Decision Documentation**:
- [ ] **Decisions documented**: Major architectural choices noted in ARCHITECTURE.md
- [ ] **Impact assessment**: How changes affect existing architecture
- [ ] **Rationale documented**: Why specific choices were made

**Consistency Checks**:
- [ ] **File paths verified**: All documented paths exist in codebase
- [ ] **Dependency alignment**: pyproject.toml matches documented constraints
- [ ] **Configuration sync**: .claude/CLAUDE.md patterns documented
- [ ] **Version updates**: Metadata reflects current state

### 5.2 LLM Independence Verification
**Test Questions for LLM Navigation**:
1. "Where is the Claude Code interface implemented?" → Should find `llm_providers/claude/claude_code_interface.py`
2. "How do I run only unit tests?" → Should reference exclusion pattern from testing strategy
3. "Where is Git automation handled?" → Should find `utils/git_operations.py`
4. "What MCP servers are required?" → Should list from constraints section

**Success Criteria**: LLM can answer all navigation questions from documentation alone.

