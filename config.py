import os

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/bot.db")
HARDCOVER_API_URL = "https://api.hardcover.app/v1/graphql"
