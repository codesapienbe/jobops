#!/bin/bash

if [ "$1" == "clean" ]; then
    rm -rf .venv
    rm -rf .pytest_cache
    rm -rf .coverage.*
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete

elif [ "$1" == "package" ]; then
    uv sync

elif [ "$1" == "test" ]; then
    uv run pytest

elif [ "$1" == "run" ]; then
    uv run jobops

elif [ "$1" == "install" ]; then
    uv sync
    uv run pyinstaller jobops.spec

elif [ "$1" == "verify" ]; then
    uv run black src/
    uv run autoflake --remove-all-unused-imports \
         --remove-unused-variables \
         --expand-star-imports \
         --recursive \
         --in-place \
         src/

    uv run vulture src/

elif [ "$1" == "deploy" ]; then
    uv run twine upload dist/*

fi
