# Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Suppression code placement | After the loop that sets all logger levels (around line 145) | The loop sets all existing loggers to the same level; placing suppression before would be overwritten |
| DEBUG log message placement | At the end of both branches (file and console logging) | Handlers must be configured before the log message can appear; both branches for consistency |
