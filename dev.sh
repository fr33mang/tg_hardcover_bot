#!/bin/bash
set -a; source .env; set +a
export DATABASE_PATH="${DATABASE_PATH:-$(pwd)/data/bot.db}"
exec uv run watchfiles --filter python "uv run bot.py" .
