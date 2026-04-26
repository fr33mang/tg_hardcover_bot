import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import TELEGRAM_BOT_TOKEN
from db import init_db
from handlers import auth, import_csv, language, search, shelves
from middleware import LanguageMiddleware

logging.basicConfig(level=logging.INFO)

_COMMANDS_EN = [
    BotCommand(command="search", description="Search for books"),
    BotCommand(command="library", description="Your reading library"),
    BotCommand(command="import", description="Import from Goodreads CSV"),
    BotCommand(command="language", description="Change language"),
    BotCommand(command="help", description="Show available commands"),
    BotCommand(command="token", description="Authorize with Hardcover token"),
    BotCommand(command="logout", description="Log out"),
]

_COMMANDS_RU = [
    BotCommand(command="search", description="Поиск книг"),
    BotCommand(command="library", description="Книжная библиотека"),
    BotCommand(command="import", description="Импорт из Goodreads CSV"),
    BotCommand(command="language", description="Сменить язык"),
    BotCommand(command="help", description="Список команд"),
    BotCommand(command="token", description="Авторизация через токен Hardcover"),
    BotCommand(command="logout", description="Выйти"),
]

_DESCRIPTION_EN = (
    "Unofficial bot for Hardcover.app — manage your reading shelves right from Telegram.\n"
    "Source: github.com/fr33mang/tg_hardcover_bot"
)
_DESCRIPTION_RU = (
    "Неофициальный бот для Hardcover.app — управляй книжными полками прямо в Telegram.\n"
    "Исходник: github.com/fr33mang/tg_hardcover_bot"
)
_SHORT_DESCRIPTION_EN = "Unofficial Hardcover.app companion. Track your reading in Telegram."
_SHORT_DESCRIPTION_RU = "Неофициальный помощник для Hardcover.app. Читай и следи за книгами в Telegram."


async def setup_bot_info(bot: Bot) -> None:
    scope = BotCommandScopeDefault()
    await bot.set_my_commands(_COMMANDS_EN, scope=scope)
    await bot.set_my_commands(_COMMANDS_RU, scope=scope, language_code="ru")
    await bot.set_my_description(_DESCRIPTION_EN)
    await bot.set_my_description(_DESCRIPTION_RU, language_code="ru")
    await bot.set_my_short_description(_SHORT_DESCRIPTION_EN)
    await bot.set_my_short_description(_SHORT_DESCRIPTION_RU, language_code="ru")


async def main():
    await init_db()

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.update.middleware(LanguageMiddleware())

    dp.include_router(language.router)
    dp.include_router(auth.router)
    dp.include_router(shelves.router)
    dp.include_router(import_csv.router)
    dp.include_router(search.router)

    await setup_bot_info(bot)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
