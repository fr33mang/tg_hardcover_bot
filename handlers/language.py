from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from db import set_language
from i18n import SUPPORTED_LANGS, get_text

router = Router()

LANG_NAMES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}


class LangSelectCallback(CallbackData, prefix="lang"):
    code: str


def _language_keyboard(current_lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=f"● {name}" if code == current_lang else name,
            callback_data=LangSelectCallback(code=code).pack(),
        )
        for code, name in LANG_NAMES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@router.message(Command("language"))
async def cmd_language(message: Message, lang: str):
    await message.answer(get_text("language_choose", lang), reply_markup=_language_keyboard(lang))


@router.callback_query(LangSelectCallback.filter())
async def language_selected(callback: CallbackQuery, callback_data: LangSelectCallback, lang: str):
    new_lang = callback_data.code
    if new_lang not in SUPPORTED_LANGS:
        await callback.answer()
        return
    await set_language(callback.from_user.id, new_lang)
    name = LANG_NAMES.get(new_lang, new_lang)
    await callback.answer(get_text("language_set", new_lang, name=name))
    await callback.message.edit_reply_markup(reply_markup=_language_keyboard(new_lang))
