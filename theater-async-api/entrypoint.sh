#!/usr/bin/env bash

# Run the application.
if [ "$API_PRODUCTION" = "true" ]; then
  eval uv run fastapi run src/main.py --host 0.0.0.0 --port 5000
else
  eval uv run fastapi dev src/main.py --host 0.0.0.0 --port 5000
fi