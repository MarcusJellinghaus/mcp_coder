# Security Policy

## Reporting a Vulnerability

Report vulnerabilities through GitHub private vulnerability reporting only: in this repository, go to **Security → Report a vulnerability**.

Do not open public issues for security problems.

## Response

Reports are handled on a best-effort basis. There is no fixed response time.

## Supported Versions

Only the latest release on PyPI receives security fixes.

## Scope

In scope are bypasses of intended restrictions, such as:

- permission gates
- the issue status workflow (e.g. promoting issues without being trusted)
- credential handling

## Threat Model

Issue bodies and comments from untrusted users are untrusted LLM input. mcp-coder only acts on issues and feedback from trusted authors (`OWNER`, `MEMBER`, `COLLABORATOR`, or allowlisted). Reports that bypass this are in scope.

See [Trust and Validation](docs/repository-setup/github.md#trust-and-validation).
