import os

from cryptography.fernet import Fernet

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/bot.db")
HARDCOVER_API_URL = "https://api.hardcover.app/v1/graphql"

_key = os.environ.get("ENCRYPTION_KEY")
if not _key:
    raise RuntimeError(
        'ENCRYPTION_KEY is not set. Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )

FERNET = Fernet(_key.encode())
