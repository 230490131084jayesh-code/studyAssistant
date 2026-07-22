#!/usr/bin/env bash
# Render sets $PORT dynamically; default to 8000 for local use.
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
