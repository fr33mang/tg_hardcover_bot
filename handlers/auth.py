import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from api import HardcoverAPI
from commands import set_user_commands
from db import delete_token, get_token, save_token
from i18n import get_text
from keyboards import all_menu_texts, main_keyboard, token_keyboard

router = Router()


class AuthStates(StatesGroup):
    waiting_for_token = State()


async def _ask_for_token(message: Message, state: FSMContext, lang: str, text_key: str) -> None:
    """Explain how to get a key and wait for it: the next plain message is treated as the key."""
    await state.set_state(AuthStates.waiting_for_token)
    await message.answer(get_text(text_key, lang), reply_markup=token_keyboard(lang), disable_web_page_preview=True)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, lang: str):
    if await get_token(message.from_user.id):
        await set_user_commands(message.bot, message.chat.id, lang)
        await message.answer(get_text("already_authorized", lang), reply_markup=main_keyboard(lang))
        return
    await _ask_for_token(message, state, lang, "start_welcome")


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext, lang: str):
    if await get_token(message.from_user.id):
        await message.answer(get_text("help_authorized", lang), reply_markup=main_keyboard(lang))
        return
    await _ask_for_token(message, state, lang, "start_welcome")


@router.message(Command("token"))
async def cmd_token(message: Message, command: CommandObject, state: FSMContext, lang: str):
    # both "/token <key>" and a bare "/token" followed by the key work
    if command.args:
        await _process_token(message, state, lang, command.args)
        return
    await _ask_for_token(message, state, lang, "token_prompt")


# a menu button tapped while we wait for a key is navigation, not a key
@router.message(AuthStates.waiting_for_token, F.text & ~F.text.startswith("/") & ~F.text.in_(all_menu_texts()))
async def token_message(message: Message, state: FSMContext, lang: str):
    await _process_token(message, state, lang, message.text)


async def _process_token(message: Message, state: FSMContext, lang: str, raw: str) -> None:
    token = raw.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    try:
        await message.delete()  # never leave the key in the chat history
    except Exception:
        pass

    if not token:
        await message.answer(get_text("token_empty", lang))
        return

    try:
        user = await HardcoverAPI(token).get_me()
    except Exception:
        logging.exception("Token check failed for user %s", message.from_user.id)
        await message.answer(get_text("token_invalid", lang), reply_markup=token_keyboard(lang))
        return
    if not user:
        await message.answer(get_text("token_invalid", lang), reply_markup=token_keyboard(lang))
        return

    await state.clear()
    username = user.get("username", "")
    await save_token(message.from_user.id, token, username, language=lang)
    await set_user_commands(message.bot, message.chat.id, lang)
    await message.answer(get_text("auth_success", lang, username=username), reply_markup=main_keyboard(lang))


@router.message(Command("logout"))
async def cmd_logout(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await delete_token(message.from_user.id)
    await message.answer(get_text("logged_out", lang), reply_markup=ReplyKeyboardRemove())
