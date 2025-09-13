@echo off
echo Running isort...
isort . --profile black --line-length 88
echo isort formatting complete.