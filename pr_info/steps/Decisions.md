# Decisions

## Shell wrappers created as executable placeholders up front

Context: the automated Step 5 run was blocked because it could not run `git add --chmod=+x` (no Bash, no MCP tool sets the git file mode).

- `tools/jenkins_builds.sh` and `tools/jenkins_download_logs.sh` are created ahead of Steps 5 and 6 as hello-world placeholders, already executable in git (commit 2f7da94). Steps 5 and 6 only replace their content; no chmod step remains. (Marcus: "If they don't, create them as dummy_helloworld.sh and the later tasks will put some real content in there.")
- The non-executable `.sh` files already on `main` (`tools/forbidden_calls_check.sh`, `tools/ruff_check.sh`, `tools/mlflow/start_mlflow.sh`) are made executable in this branch. (Marcus: "Can you take care of all? If they exist, do the chmod.")
