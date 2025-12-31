# Step 5: Documentation Updates for Caching Functionality

## Objective
Update existing documentation to describe the new GitHub API caching functionality, configuration options, and troubleshooting guidance.

## LLM Prompt
```
Based on the GitHub API caching implementation summary, update existing documentation to include caching functionality.

Requirements:
- Add caching section to relevant existing documentation files
- Document configuration options (cache_refresh_minutes, --force-refresh)
- Include troubleshooting guidance for cache-related issues
- Explain cache behavior and performance benefits
- Follow existing documentation patterns and style
- Keep documentation user-focused and practical

Refer to the summary document for technical details and architecture context.
```

## WHERE
- **Files**: Look for existing coordinator documentation (README.md, docs/, etc.)
- **New Sections**: Add caching information to existing coordinator documentation
- **Configuration Docs**: Update config documentation if it exists

## WHAT
### Documentation Sections to Add
```markdown
## Caching
- Overview of GitHub API caching
- Configuration options
- Performance benefits
- Troubleshooting

## Configuration
- cache_refresh_minutes setting
- Default values and recommendations

## CLI Options
- --force-refresh flag usage and scenarios
```

### Content Areas
- **Cache Behavior**: How incremental fetching works
- **Duplicate Protection**: 1-minute window explanation
- **Configuration**: cache_refresh_minutes setting
- **CLI Flags**: --force-refresh usage
- **Troubleshooting**: Common cache issues and solutions
- **Performance**: Expected API call reduction benefits

## HOW
### Integration Points
- **Find existing docs**: Search for coordinator documentation files
- **Follow patterns**: Use existing documentation style and structure
- **User perspective**: Focus on practical usage, not implementation details
- **Examples**: Include example configurations and use cases

### Documentation Structure
```markdown
# Coordinator Command

## Overview
[existing content]

## Caching (NEW SECTION)
The coordinator includes GitHub API caching to reduce API calls...

### Configuration
Add to your ~/.mcp_coder/config.toml:
```toml
[coordinator]
cache_refresh_minutes = 1440  # 24 hours (default)
```

### CLI Options
- `--force-refresh`: Bypass all caching and fetch fresh data
```

## ALGORITHM
```
1. Locate existing coordinator documentation files
2. Identify appropriate sections for caching information
3. Add caching overview with benefits explanation
4. Document configuration options with examples
5. Add troubleshooting section for common cache issues
6. Include performance expectations and recommendations
```

## DATA
### Documentation Content
- **Cache Overview**: Non-technical explanation of caching benefits
- **Configuration**: TOML examples with recommended values
- **CLI Usage**: Command examples with --force-refresh flag
- **Troubleshooting**: Common issues and solutions

### Configuration Examples
```toml
# Default configuration (24-hour refresh)
[coordinator]
cache_refresh_minutes = 1440

# More frequent refresh for active development
[coordinator]  
cache_refresh_minutes = 60

# Conservative refresh for stable repositories
[coordinator]
cache_refresh_minutes = 2880  # 48 hours
```

### CLI Examples
```bash
# Normal run (uses cache)
mcp-coder coordinator run --repo my_repo

# Force fresh data (bypasses cache)
mcp-coder coordinator run --repo my_repo --force-refresh

# Run all repositories with forced refresh
mcp-coder coordinator run --all --force-refresh
```

## Implementation Notes
- **User-focused**: Explain benefits and usage, not implementation details
- **Practical examples**: Show real configuration and command scenarios  
- **Troubleshooting**: Help users resolve common cache-related issues
- **Performance guidance**: Set expectations for API call reduction
- **Integration**: Blend seamlessly with existing documentation style