#!/bin/bash
# Dev runner: restarts the bot on any .py change.
# Run python directly (not via `uv run bot.py`): watchfiles can only kill the process it
# spawned, and a `uv run` wrapper leaves the real python alive — every reload then adds
# one more poller on the same bot token, and Telegram splits updates between them.
set -a; source .env; set +a
export DATABASE_PATH="${DATABASE_PATH:-$(pwd)/data/bot.db}"
uv sync -q
exec uv run watchfiles --filter python ".venv/bin/python bot.py" .
