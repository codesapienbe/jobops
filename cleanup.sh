#!/bin/bash

uv run vulture \
  src/jobops .vulture_whitelist.py \
  --min-confidence 80 \
  --exclude "tests/*,scripts/*" \
  --sort-by-size

  