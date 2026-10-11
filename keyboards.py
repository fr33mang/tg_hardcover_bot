from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from callbacks import MoreCallback
from config import HARDCOVER_NEW_KEY_URL
from i18n import SUPPORTED_LANGS, get_text

MENU_READING = "btn_menu_reading"
MENU_LIBRARY = "btn_menu_library"
MENU_SEARCH = "btn_menu_search"
MENU_MORE = "btn_menu_more"

_LAYOUT = [[MENU_READING, MENU_LIBRARY], [MENU_SEARCH, MENU_MORE]]


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """The persistent reply keyboard: global navigation, always visible once authorized."""
    rows = [[KeyboardButton(text=get_text(key, lang)) for key in row] for row in _LAYOUT]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def menu_texts(key: str) -> set[str]:
    """Every translation of a menu button: the keyboard may have been sent before a language change."""
    return {get_text(key, lang) for lang in SUPPORTED_LANGS}


def all_menu_texts() -> set[str]:
    texts: set[str] = set()
    for row in _LAYOUT:
        for key in row:
            texts |= menu_texts(key)
    return texts


def token_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=get_text("btn_create_key", lang), url=HARDCOVER_NEW_KEY_URL)]]
    )


def more_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=get_text("btn_more_language", lang), callback_data=MoreCallback(action="language").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_more_import", lang), callback_data=MoreCallback(action="import").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_more_token", lang), callback_data=MoreCallback(action="token").pack()
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_more_logout", lang), callback_data=MoreCallback(action="logout").pack()
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
