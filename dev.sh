#!/bin/bash
set -a; source .env; set +a
exec uv run watchfiles --filter python "uv run bot.py" .
