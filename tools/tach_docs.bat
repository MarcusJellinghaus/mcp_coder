@echo off
REM Generate architecture documentation (dependency graph and report)
REM Usage: tools\generate_architecture_docs.bat
REM
REM Creates:
REM   - docs/architecture/dependency_graph.html
REM   - docs/architecture/dependency_report.html

python "%~dp0tach_docs.py"
