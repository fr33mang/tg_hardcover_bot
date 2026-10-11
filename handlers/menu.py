"""The reply keyboard (global navigation) and the settings screen behind ⚙️."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from api import HardcoverAPI
from callbacks import MoreCallback
from config import HARDCOVER_SCOPES
from db import delete_token, get_token, set_nav_context
from handlers.auth import AuthStates
from handlers.import_csv import ImportStates
from handlers.language import language_keyboard
from handlers.shelves import render_library, render_shelf
from i18n import get_text
from keyboards import (
    MENU_LIBRARY,
    MENU_MORE,
    MENU_READING,
    MENU_SEARCH,
    menu_texts,
    more_keyboard,
    token_keyboard,
)
from screen import show_screen

router = Router()

READING_STATUS_ID = 2


@router.message(F.text.in_(menu_texts(MENU_READING)))
async def menu_reading(message: Message, state: FSMContext, lang: str):
    await state.clear()
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer(get_text("auth_required", lang))
        return
    api = HardcoverAPI(token)
    try:
        screen = await render_shelf(api, lang, READING_STATUS_ID, 0)
    except Exception as e:
        await message.answer(get_text("error_generic", lang, e=e))
        return
    await set_nav_context(message.from_user.id, {"kind": "shelf", "id": READING_STATUS_ID, "offset": 0})
    if screen is None:
        await show_screen(get_text("reading_empty", lang), None, message=message)
        return
    await show_screen(*screen, message=message)


@router.message(F.text.in_(menu_texts(MENU_LIBRARY)))
async def menu_library(message: Message, state: FSMContext, lang: str):
    await state.clear()
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer(get_text("auth_required", lang))
        return
    api = HardcoverAPI(token)
    try:
        text, kb = await render_library(api, lang)
    except Exception as e:
        await message.answer(get_text("error_generic", lang, e=e))
        return
    await set_nav_context(message.from_user.id, None)
    await show_screen(text, kb, message=message)


@router.message(F.text.in_(menu_texts(MENU_SEARCH)))
async def menu_search(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await message.answer(get_text("search_prompt", lang))


@router.message(F.text.in_(menu_texts(MENU_MORE)))
async def menu_more(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await show_screen(get_text("more_title", lang), more_keyboard(lang), message=message)


@router.callback_query(MoreCallback.filter(F.action == "language"))
async def more_language(callback: CallbackQuery, lang: str):
    await show_screen(get_text("language_choose", lang), language_keyboard(lang), callback=callback)
    await callback.answer()


@router.callback_query(MoreCallback.filter(F.action == "import"))
async def more_import(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(ImportStates.waiting_for_file)
    await callback.message.answer(get_text("import_prompt", lang))
    await callback.answer()


@router.callback_query(MoreCallback.filter(F.action == "token"))
async def more_token(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(AuthStates.waiting_for_token)
    text = get_text("token_prompt", lang, scopes=" ".join(HARDCOVER_SCOPES))
    await callback.message.answer(text, reply_markup=token_keyboard(lang), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(MoreCallback.filter(F.action == "logout"))
async def more_logout(callback: CallbackQuery, state: FSMContext, lang: str):
    await state.clear()
    await delete_token(callback.from_user.id)
    await callback.message.answer(get_text("logged_out", lang), reply_markup=ReplyKeyboardRemove())
    await callback.answer()
