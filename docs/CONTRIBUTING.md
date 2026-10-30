# Contributing to MCP Coder

MCP Coder is developed with MCP Coder: work starts from an issue and follows the
[Development Process](processes-prompts/development-process.md). The repo rules for the LLM
(tools, checks, commits) are in [`.claude/CLAUDE.md`](../.claude/CLAUDE.md).

Specific to this repo:

- **Running your local source:** [Environments](environments/environments.md#special-case-mcp-coder-working-on-itself), [Installation](getting-started/installation.md)
- **Checks and CI:** [Quality and Security Checks](repository-setup/quality-and-security-checks.md)
- **Moving code, splitting large files:** [Safe Refactoring Guide](processes-prompts/refactoring-guide.md)
- **Keeping the architecture overview current:** [Architecture Maintenance](architecture/architecture-maintenance.md)
- **Slow or flaky tests:** [Slow Test Review](tests/slow-test-review-methodology.md)
- **Maintainer-only scripts (mlflow, Jenkins logs, local reinstall):** [Internal files](repository-setup/internal.md)

Report vulnerabilities as described in [SECURITY.md](../SECURITY.md).
