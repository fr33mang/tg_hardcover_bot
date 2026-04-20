# Hardcover Telegram Bot

Telegram bot for [Hardcover.app](https://hardcover.app) — search books, manage your library and lists.

> **Disclaimer:** This is an unofficial bot and is not affiliated with or endorsed by Hardcover. It uses the [Hardcover public API](https://hardcover.app/account/api).

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
| `/token <your_token>` | Authenticate with Hardcover |
| `/library` | View your library by status |
| `/search <query>` | Search for books |
| `/import` | Import library from Goodreads CSV |

You can also just send any text message to search.

## Stack

- Python 3.12
- [aiogram 3](https://docs.aiogram.dev/)
- [Hardcover GraphQL API](https://hardcover.app/account/api)
- SQLite (via aiosqlite)
