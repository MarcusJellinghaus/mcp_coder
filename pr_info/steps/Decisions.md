# Project Plan Decisions

## Decisions Made During Plan Review

### 1. Broader Pattern Analysis
**Decision**: Scan everything that is part of CLI (Option A from the scan results)  
**When Discussed**: When I asked about analyzing the entire codebase for similar architectural violations  
**Your Response**: "Scan everything that is part of CLI"
**Result**: Found only the single violation we're already addressing

### 2. LLM Method Parameter Architecture
**Decision**: Change to separate `provider: str, method: str` parameters  
**When Discussed**: When I asked about keeping current function signature vs changing to separate parameters  
**Your Response**: "B) Change to separate `provider: str, method: str` parameters"  
**Additional**: "Keep llm_method preferably on the cli layer, and offer there a small shared utility (also to be used by prompt, implement)"

### 3. Shared CLI Utility Location
**Decision**: Create `src/mcp_coder/cli/utils.py` for CLI-specific utilities  
**When Discussed**: When I asked where to put the shared CLI utility function  
**Your Response**: "A" (Create new cli/utils.py file)

### 4. Implementation Scope Expansion
**Decision**: Expand scope to update all CLI commands for consistency  
**When Discussed**: When I asked about expanding the project to include updating all CLI commands  
**Your Response**: "A - which other cli commands need to be changed, and how?"

### 5. Workflow Function Signatures
**Decision**: Update all workflow functions to use `provider, method` parameters  
**When Discussed**: When I asked whether to update all workflow functions for consistency  
**Your Response**: "A" (Yes - update all workflow functions for consistency)

### 6. Implementation Strategy
**Decision**: Break into 6-8 smaller steps for better validation at each stage  
**When Discussed**: When I asked about implementation strategy given the expanded scope  
**Your Response**: "B" (Break into 6-8 smaller steps)

### 7. Final Step Granularity
**Decision**: Keep the 6-step approach for good balance of safety and progress  
**When Discussed**: When I asked about the step granularity  
**Your Response**: "A" (Keep this 6-step approach)

## Scope Evolution
- Started as simple function move to fix architectural violation
- Evolved to comprehensive parameter architecture improvement
- Now affects CLI commands, workflows, and utils layers
- Creates shared utilities and eliminates code duplication
- Maintains backward compatibility while improving internal architecture
