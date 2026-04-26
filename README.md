# Hardcover Telegram Bot

Telegram bot for [Hardcover.app](https://hardcover.app) — search books, manage your library and lists.

> **Disclaimer:** This is an unofficial bot and is not affiliated with or endorsed by Hardcover. It uses the [Hardcover public API](https://hardcover.app/account/api).

The bot is available at [@hardcoverapp_bot](https://t.me/hardcoverapp_bot).

## Features

- **Search** — find books by title or ISBN, browse paginated results
- **Book details** — cover, description, rating, reading status
- **Library** — view all 6 reading statuses with book counts
- **Lists** — browse and manage your Hardcover lists
- **Goodreads import** — import your library from a Goodreads CSV export
- **Inline mode** — search books from any chat via `@botname query`

## Setup

1. Clone the repo and install dependencies:
   ```bash
   cp .env.example .env
   uv sync
   ```

2. Fill in `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

3. Get your Hardcover API token at [hardcover.app/account/api](https://hardcover.app/account/api)

4. Run:
   ```bash
   uv run python bot.py
   ```

## Commands

| Command | Description |
|---|---|
| `/search <query>` | Search for books |
| `/library` | View your library by reading status |
| `/import` | Import library from Goodreads CSV |
| `/language` | Change the bot language |
| `/help` | Show available commands |
| `/token` | Authenticate with Hardcover |
| `/logout` | Log out |

You can also just send any text message to search.

## Adding a New Language

Translations live in the `locales/` directory. Each language is a single Python file with a `STRINGS` dict.

**Steps to add a new language:**

1. **Copy the English locale file** and rename it to the [IETF language tag](https://en.wikipedia.org/wiki/IETF_language_tag) prefix (e.g. `de` for German):
   ```bash
   cp locales/en.py locales/de.py
   ```

2. **Translate the values** in `locales/de.py`. Do not change the keys — they must match exactly across all locale files. Keep format placeholders like `{username}` as-is.

3. **Register the language** in `i18n.py`:
   ```python
   from locales import en, ru, de  # add de

   SUPPORTED_LANGS = {
       "ru": ru.STRINGS,
       "en": en.STRINGS,
       "de": de.STRINGS,  # add this line
   }
   ```

4. **Add the display name** in `handlers/language.py`:
   ```python
   LANG_NAMES = {
       "ru": "🇷🇺 Русский",
       "en": "🇬🇧 English",
       "de": "🇩🇪 Deutsch",  # add this line
   }
   ```

**Notes:**
- If a key is missing in a locale file, the bot automatically falls back to English.
- Telegram's `language_code` is used to auto-detect the language for new users. They can always override it with `/language`.

## Stack

- Python 3.12
- [aiogram 3](https://docs.aiogram.dev/)
- [Hardcover GraphQL API](https://hardcover.app/account/api)
- SQLite (via aiosqlite)
