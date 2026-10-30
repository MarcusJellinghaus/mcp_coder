# MCP Coder

**Turn GitHub issues into reviewed pull requests with a staged, LLM-driven process: full control and visibility, and you only write the issues.**

[![CI](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/mcp-coder)](https://pypi.org/project/mcp-coder/) [![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/MarcusJellinghaus/mcp_coder/main/pyproject.toml)](https://pypi.org/project/mcp-coder/) [![License](https://img.shields.io/github/license/MarcusJellinghaus/mcp_coder)](LICENSE)

Every change to MCP Coder itself passes these checks ([details](docs/repository-setup/quality-and-security-checks.md)):

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/) [![pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![architecture](https://img.shields.io/badge/architecture-enforced-blue)](docs/architecture/enforcement.md) [![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MarcusJellinghaus/9a7892066964f11765a07d74285ad104/raw/mcp_coder-coverage.json)](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/ci.yml) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/MarcusJellinghaus/mcp_coder/badge)](https://scorecard.dev/viewer/?uri=github.com/MarcusJellinghaus/mcp_coder) [![CodeQL](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/MarcusJellinghaus/mcp_coder/actions/workflows/github-code-scanning/codeql)

## What it does

- **Minimal input.** You write and refine issues, approve at the review gates and merge. Everything else can run unattended; failures come back to you as labelled issues.
- **Control and visibility.** Each stage ends in a written hand-over document: the refined issue, the plan, step files, commits, review comments. You can inspect or correct at every point.
- **Quality gates on every step.** pylint, mypy and pytest run after each implementation step, mcp-coder re-checks mypy itself once all steps are done, and every plan step carries its own tests, planned before the code. Tests are part of the review.
- **Fewer tokens, shorter conversations.** Instead of one large implementation conversation, the work is split into small steps, each starting with a fresh context and only the hand-over documents it needs. This should reduce token consumption.
- **Follow-up after the PR.** The coordinator watches open PRs: merge conflicts and failing CI are fixed automatically, review comments are routed to you.
- **Trust boundaries.** `/approve` and PR feedback only count from trusted authors (owner, member, collaborator). A watchdog moves crashed jobs to a failure label, so no issue silently sits at "in progress".

## Why a structured process

Spec-driven development, applied to GitHub issues:

`issue → refined spec → reviewed plan → implementation in small verified steps → reviewed code → PR`

- A GitHub status label on the issue is the only workflow state. It decides what runs next.
- Plan and code review are explicit approval points. You can do them interactively, or enable an optional automated review that hands over to you when it needs a human.
- The LLM does the creative work; MCP Coder owns the process around it and verifies the result itself instead of trusting it.
- The LLM reaches files, git, GitHub and the quality checks only through [MCP](https://modelcontextprotocol.io) servers ([`mcp-workspace`](https://github.com/MarcusJellinghaus/mcp-workspace), [`mcp-tools-py`](https://github.com/MarcusJellinghaus/mcp-tools-py)), configured per repository in `.mcp.json` ([details](docs/repository-setup/claude-code.md)).
- Unattended runs are driven by `mcp-coder coordinator`, which polls issues and dispatches workflows, typically as Jenkins jobs.
- Interactive stages are driven by `mcp-coder vscodeclaude`, which opens a VS Code Claude session for each issue that needs you.

```mermaid
flowchart LR
    I([Issue]) --> A[Analyse and approve]
    A --> P[Create plan]
    P --> PR{Plan review}
    PR --> M[Implement step by step<br/>checks + tests per step]
    M --> CR{Code review}
    CR --> PUB[Create PR]
    PUB --> MG([Merge])

    classDef human fill:#fbbf24,stroke:#b45309,color:#111
    classDef auto fill:#4ade80,stroke:#15803d,color:#111
    class A,PR,CR,MG human
    class P,M,PUB auto
```

Yellow: you, in an interactive Claude session opened by `vscodeclaude` (or approving on GitHub). Green: automated by the coordinator. Full state machine, labels and failure handling: [Development Process](docs/processes-prompts/development-process.md).

## Status and scope

| Level | What |
|---|---|
| Works well | Python projects, GitHub, Claude Code |
| Experimental | GitHub Copilot CLI, LangChain backends (OpenAI, Gemini, Anthropic API, Ollama, …) |
| Prototype | [`iCoder`](docs/iCoder.md), an alternative interactive terminal interface |
| Planned | Other programming languages, general LLM support |

The label-driven process itself is language-agnostic. Python is the supported target for now because `implement`, the installer and the architecture checks call Python tools. GitHub is the only supported forge.

## Getting started

Requirements: Python 3.11+, Git, a GitHub-hosted repository and [Claude Code CLI](https://code.claude.com/docs) (recommended; [Copilot CLI](https://docs.github.com/copilot/how-tos/use-copilot-agents/use-copilot-cli) is experimental).

```bash
pip install mcp-coder
```

Other install paths (editable dev install, pinned GitHub ref, separate environment): [Installation Guide](docs/getting-started/installation.md).

### Set up a repository (once)

The full checklist, with every config key, is in [Repository Setup](docs/repository-setup/README.md). In short:

1. Put a GitHub token in `~/.mcp_coder/config.toml` ([Configuration](docs/configuration/config.md)).
2. Create the status labels with `mcp-coder gh-tool define-labels`, and the GitHub Actions that label new issues and handle `/approve` with `--generate-github-actions` ([Label Setup](docs/getting-started/label-setup.md)).
3. Deploy the Claude skills and agents with `mcp-coder init`, and add `.claude/CLAUDE.md`, `.mcp.json` and `docs/architecture/architecture.md` to the repository.
4. Configure how stages run: `[vscodeclaude]` for interactive sessions ([guide](docs/coordinator-vscodeclaude.md)), `[jenkins]` and `[coordinator.repos.<name>]` for unattended runs ([Jenkins setup](docs/repository-setup/jenkins.md)). Without Jenkins, run the stages by hand.
5. Check it all with `mcp-coder verify`.

### Work with it

1. **Write an issue.** It gets `status-01:created` automatically.
2. **Assign it to yourself and refine it.** `mcp-coder vscodeclaude launch` opens a VS Code Claude session for every issue that is assigned to you (the GitHub user of your token) and has a status that needs a human. It starts the right slash command: `/issue_analyse` then `/discuss` for a new issue. Approve in the session (`/issue_approve`) or comment `/approve` on GitHub.
3. **Let the coordinator run the next stage.** `mcp-coder coordinator --all` dispatches planning, implementation and PR creation as the label advances.
4. **Review the plan and the code.** `vscodeclaude` opens sessions again for `status-04:plan-review` and `status-07:code-review`, again only for issues assigned to you. Use `/plan_review` and `/implementation_review`, or the `_supervisor` variants that run the review through subagents, then approve.
5. **Merge.** Conflicts, failing CI and review comments come back as labelled issues.

Slash commands per stage: [Development Process](docs/processes-prompts/development-process.md) and the [cheat sheet](docs/processes-prompts/claude_cheat_sheet.md). Running a single stage by hand (`create-plan`, `implement`, `create-pr`): [CLI Reference](docs/cli-reference.md). Details on sessions and the coordinator: [Coordinator and VSCodeClaude](docs/coordinator-vscodeclaude.md).

## Documentation

- [Development Process](docs/processes-prompts/development-process.md): stages, labels, slash commands, failure handling
- [Repository Setup](docs/repository-setup/README.md): labels, GitHub Actions, MCP configuration, Jenkins
- [Label Setup](docs/getting-started/label-setup.md): the status labels and the `/approve` workflow
- [Coordinator and VSCodeClaude](docs/coordinator-vscodeclaude.md): unattended runs and interactive sessions
- [Slash command cheat sheet](docs/processes-prompts/claude_cheat_sheet.md)
- [CLI Reference](docs/cli-reference.md) and [Configuration](docs/configuration/config.md)
- [Architecture](docs/architecture/architecture.md) and [why it is enforced](docs/architecture/enforcement.md)
- [Contributing](docs/CONTRIBUTING.md): developing MCP Coder itself
- [Full documentation index](docs/README.md)

## Related projects

- [mcp-tools-py](https://github.com/MarcusJellinghaus/mcp-tools-py): MCP server for code quality checks (pylint, mypy, pytest, formatting)
- [mcp-workspace](https://github.com/MarcusJellinghaus/mcp-workspace): MCP server for file operations, git and GitHub
- [mcp-coder-utils](https://github.com/MarcusJellinghaus/mcp-coder-utils): shared subprocess, logging and redaction helpers

## Security and license

Report vulnerabilities as described in [SECURITY.md](SECURITY.md). Released under the terms in [LICENSE](LICENSE).
