"""Bot command menu (the "/" list and the Menu button).

Telegram clients do not reliably pick up a global ``setMyCommands`` for chats that
were already open before the commands existed — the user may never see the menu.
A per-chat ``setMyCommands`` is pushed to that user's clients immediately, so we set
commands both globally (for first-time openers) and per chat (on /start, auth and
language change) in the user's bot language.
"""

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from i18n import DEFAULT_LANG, SUPPORTED_LANGS, get_text

_COMMAND_KEYS = ["search", "library", "import", "language", "help", "token", "logout"]


def commands_for(lang: str) -> list[BotCommand]:
    return [BotCommand(command=key, description=get_text(f"cmd_{key}", lang)) for key in _COMMAND_KEYS]


async def set_global_commands(bot: Bot) -> None:
    scope = BotCommandScopeDefault()
    await bot.set_my_commands(commands_for(DEFAULT_LANG), scope=scope)
    for lang in SUPPORTED_LANGS:
        await bot.set_my_commands(commands_for(lang), scope=scope, language_code=lang)


async def set_user_commands(bot: Bot, chat_id: int, lang: str) -> None:
    await bot.set_my_commands(commands_for(lang), scope=BotCommandScopeChat(chat_id=chat_id))
