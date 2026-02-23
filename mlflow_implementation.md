# MLflow Implementation Plan

## Overview
Add optional MLflow integration to log Claude Code conversations for better visibility and analytics.

## Architecture Design

### Principles
- **Optional**: MLflow features are completely optional
- **Graceful fallback**: Code works normally if MLflow is not installed
- **Non-invasive**: Minimal changes to existing code paths
- **Configurable**: Users control when and how MLflow logging occurs

### Integration Points
1. **Configuration**: Extend `config.toml` to include MLflow settings
2. **Logging**: Hook into existing LLM call infrastructure
3. **Storage**: Log alongside existing JSON storage, not replacing it

## Implementation Plan

### Phase 1: Foundation (Minimal Viable Product)
**Goal**: Basic MLflow logging with graceful fallback

#### 1.1 Configuration Module
- [ ] **File**: `src/mcp_coder/config/mlflow_config.py`
- [ ] **Purpose**: Load MLflow settings from `config.toml`
- [ ] **Integration**: Use `get_config_values()` from `utils.user_config`
- [ ] **Environment Variables**: Support `MLFLOW_TRACKING_URI`, `MLFLOW_EXPERIMENT_NAME`
- [ ] **Schema**:
  ```python
  @dataclass
  class MLflowConfig:
      enabled: bool = False
      tracking_uri: Optional[str] = None
      experiment_name: str = "claude-conversations"
  ```

#### 1.2 MLflow Logger Module
- [ ] **File**: `src/mcp_coder/llm/mlflow_logger.py`
- [ ] **Purpose**: Optional MLflow logging with graceful fallback
- [ ] **Key Features**:
  - [ ] Detect if MLflow is installed
  - [ ] Log experiment runs with conversation metadata
  - [ ] Store conversation JSON as artifacts
  - [ ] Handle all MLflow errors gracefully

#### 1.3 Integration Hook
- [ ] **File**: `src/mcp_coder/llm/providers/claude/logging_utils.py` (extend existing)
- [ ] **Purpose**: Add MLflow logging calls to existing log functions
- [ ] **Changes**:
  - [ ] `log_llm_request()`: Start MLflow run
  - [ ] `log_llm_response()`: Log metrics and end run
  - [ ] `log_llm_error()`: Log error and end run

#### 1.4 Session Storage Integration
- [ ] **File**: `src/mcp_coder/llm/storage/session_storage.py` (extend existing)
- [ ] **Purpose**: Trigger MLflow logging when sessions are stored
- [ ] **Changes**: Add optional MLflow logging call in `store_session()`

### Phase 2: Enhanced Features
**Goal**: Rich analytics and better user experience

#### 2.1 Advanced Metrics
- Conversation complexity scoring
- Topic classification
- Error rate tracking
- Performance trends

#### 2.2 Custom MLflow UI Components
- Conversation viewer component
- Search and filter enhancements
- Cost tracking dashboard

#### 2.3 Batch Processing
- Retroactive logging of existing JSON files
- Bulk analysis tools

### Phase 3: Advanced Analytics
**Goal**: AI-powered insights and recommendations

#### 3.1 Pattern Analysis
- Identify successful prompting patterns
- Suggest optimizations
- Detect recurring issues

## File Changes Required

### New Files
- [ ] `src/mcp_coder/config/mlflow_config.py` - MLflow configuration
- [ ] `src/mcp_coder/llm/mlflow_logger.py` - MLflow logging logic
- [ ] `tests/config/test_mlflow_config.py` - Config tests
- [ ] `tests/llm/test_mlflow_logger.py` - Logger tests
- [x] `docs/configuration/mlflow-integration.md` - User documentation

### Modified Files
- [x] `pyproject.toml` - Add MLflow dependency
- [ ] `src/mcp_coder/llm/providers/claude/logging_utils.py` - Add MLflow hooks
- [ ] `src/mcp_coder/llm/storage/session_storage.py` - Add MLflow logging
- [ ] `src/mcp_coder/config/__init__.py` - Export MLflow config

## Test Strategy

### Unit Tests
- **MLflow config loading**: Test valid/invalid configurations
- **Graceful fallback**: Test behavior when MLflow not installed
- **Error handling**: Test all MLflow error scenarios
- **Integration points**: Test hooks in logging_utils and session_storage

### Integration Tests
- **End-to-end logging**: Test full conversation logging flow
- **UI verification**: Test that logged data appears correctly in MLflow UI
- **Configuration scenarios**: Test different tracking URI types

### Test Markers
```python
# In pyproject.toml
"mlflow_integration: tests requiring MLflow installation and setup"
```

## Configuration Schema

### `config.toml` Extension
```toml
[mlflow]
enabled = true
tracking_uri = "file://./mlruns"
experiment_name = "claude-conversations"

# Optional: Run tags as key-value pairs
[mlflow.run_tags]
project = "my-project"
environment = "development"
```

### Environment Variable Support
```bash
# Override config.toml settings
export MLFLOW_TRACKING_URI="http://localhost:5000"
export MLFLOW_EXPERIMENT_NAME="production-conversations"
```

## Rollout Strategy

### Development
1. Implement Phase 1 on feature branch
2. Test locally with sample conversations
3. Add comprehensive unit tests
4. Integration testing with MLflow UI

### User Adoption
1. **Opt-in**: Users must explicitly enable MLflow in config
2. **Documentation**: Clear setup and usage guides
3. **Examples**: Sample configurations and use cases
4. **Migration**: Tool to import existing JSON conversations

## Risk Mitigation

### Performance Impact
- **Async logging**: Don't block main conversation flow
- **Batch operations**: Group related log calls
- **Resource limits**: Prevent excessive disk/memory usage

### Dependency Management
- **Optional import**: Use try/except for all MLflow imports
- **Version compatibility**: Test with multiple MLflow versions
- **Fallback behavior**: Full functionality without MLflow

### Data Privacy
- **Local storage**: Default to local file system
- **Configurable**: Users control where data goes
- **Sensitive data**: Option to exclude prompt content

## Success Metrics

#### Phase 1
- [ ] MLflow integration works for basic conversation logging
- [ ] Zero impact when disabled or not installed
- [ ] All existing tests continue to pass
- [ ] Documentation complete and tested

### Phase 2
- [ ] Users report improved conversation visibility
- [ ] Analytics provide actionable insights
- [ ] Performance impact < 5% for normal operations

### Phase 3
- [ ] Pattern recognition helps users improve prompting
- [ ] Cost tracking helps optimize usage
- [ ] Integration becomes standard part of workflow

## Questions for Discussion

1. **Storage location**: Should we default to project-local `./mlruns` or user home directory?
2. **Experiment organization**: How should we group conversations? By date, project, or user-defined?
3. **Sensitive data**: Should we provide options to exclude prompt content from logging?
4. **Retention**: Should we implement automatic cleanup of old MLflow data?
5. **Remote MLflow**: Do we need to support MLflow server authentication?