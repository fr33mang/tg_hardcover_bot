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
        if user:
            lang = await get_language(user.id)
            if lang == DEFAULT_LANG:
                detected = detect_lang(user.language_code)
                if detected != DEFAULT_LANG:
                    lang = detected
        else:
            lang = DEFAULT_LANG
        data["lang"] = lang
        return await handler(event, data)
