from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from db import get_language
from i18n import DEFAULT_LANG, detect_lang


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        lang = None
        if user:
            # a known user's own choice wins; a newcomer gets their Telegram UI language
            lang = await get_language(user.id) or detect_lang(user.language_code)
        data["lang"] = lang or DEFAULT_LANG
        return await handler(event, data)
