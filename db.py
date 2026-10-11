import json

import aiosqlite

from config import DATABASE_PATH, FERNET
from i18n import DEFAULT_LANG

_lang_cache: dict[int, str] = {}


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                bearer_token TEXT NOT NULL DEFAULT '',
                hardcover_username TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()
        for ddl in (
            f"ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT '{DEFAULT_LANG}'",
            "ALTER TABLE users ADD COLUMN screen_message_id INTEGER",
            "ALTER TABLE users ADD COLUMN nav_context TEXT",
        ):
            try:
                await db.execute(ddl)
                await db.commit()
            except Exception:
                pass  # column already exists


async def save_token(telegram_id: int, token: str, username: str | None = None):
    encrypted = FERNET.encrypt(token.encode()).decode()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO users (telegram_id, bearer_token, hardcover_username)
               VALUES (?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                 bearer_token=excluded.bearer_token,
                 hardcover_username=excluded.hardcover_username""",
            (telegram_id, encrypted, username),
        )
        await db.commit()


async def get_token(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT bearer_token FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return FERNET.decrypt(row[0].encode()).decode()


async def delete_token(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.commit()
    _lang_cache.pop(telegram_id, None)


async def get_language(telegram_id: int) -> str:
    if telegram_id in _lang_cache:
        return _lang_cache[telegram_id]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            lang = row[0] if row else DEFAULT_LANG
    _lang_cache[telegram_id] = lang
    return lang


async def set_language(telegram_id: int, lang: str) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (lang, telegram_id),
        )
        await db.commit()
    _lang_cache[telegram_id] = lang


# --- screen state: the one "screen" message per chat and where "back" leads ---


async def get_screen_message(telegram_id: int) -> int | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT screen_message_id FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_screen_message(telegram_id: int, message_id: int | None) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET screen_message_id = ? WHERE telegram_id = ?", (message_id, telegram_id))
        await db.commit()


async def get_nav_context(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT nav_context FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or not row[0]:
                return None
            try:
                return json.loads(row[0])
            except ValueError:
                return None


async def set_nav_context(telegram_id: int, ctx: dict | None) -> None:
    payload = json.dumps(ctx, ensure_ascii=False) if ctx else None
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET nav_context = ? WHERE telegram_id = ?", (payload, telegram_id))
        await db.commit()
