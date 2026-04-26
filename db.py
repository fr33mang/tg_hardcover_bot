import aiosqlite

from config import DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                bearer_token TEXT NOT NULL,
                hardcover_username TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()
        try:
            await db.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
            await db.commit()
        except Exception:
            pass  # column already exists


async def save_token(telegram_id: int, token: str, username: str | None = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """INSERT INTO users (telegram_id, bearer_token, hardcover_username)
               VALUES (?, ?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET
                 bearer_token=excluded.bearer_token,
                 hardcover_username=excluded.hardcover_username""",
            (telegram_id, token, username),
        )
        await db.commit()


async def get_token(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT bearer_token FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def delete_token(telegram_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def get_language(telegram_id: int) -> str:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT language FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else "en"


async def set_language(telegram_id: int, lang: str) -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (lang, telegram_id),
        )
        await db.commit()
