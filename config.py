import os

from cryptography.fernet import Fernet

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DATABASE_PATH = os.environ.get("DATABASE_PATH", "/data/bot.db")
HARDCOVER_API_URL = "https://api.hardcover.app/v1/graphql"

# Scopes the bot needs. The link opens Hardcover's "New API key" form with them pre-checked.
HARDCOVER_SCOPES = ["read:me", "read:catalog", "read:library", "write:library", "read:lists", "write:lists"]
HARDCOVER_NEW_KEY_URL = "https://hardcover.app/account/api/keys/new?scope=" + "+".join(HARDCOVER_SCOPES)

_key = os.environ.get("ENCRYPTION_KEY")
if not _key:
    raise RuntimeError(
        'ENCRYPTION_KEY is not set. Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )

FERNET = Fernet(_key.encode())
