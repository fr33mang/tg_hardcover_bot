from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from api import HardcoverAPI
from db import delete_token, get_token, save_token
from i18n import get_text

router = Router()


class AuthStates(StatesGroup):
    waiting_for_token = State()


@router.message(Command("start"))
async def cmd_start(message: Message, lang: str):
    has_token = await get_token(message.from_user.id)
    if has_token:
        await message.answer(get_text("already_authorized", lang))
        return
    await message.answer(get_text("start_welcome", lang), parse_mode="HTML")


@router.message(Command("token"))
async def cmd_token(message: Message, state: FSMContext, lang: str):
    await state.set_state(AuthStates.waiting_for_token)
    await message.answer(get_text("token_prompt", lang), parse_mode="HTML")


@router.message(AuthStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext, lang: str):
    await state.clear()
    token = message.text.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    try:
        await message.delete()
    except Exception:
        pass

    if not token:
        await message.answer(get_text("token_empty", lang))
        return

    try:
        api = HardcoverAPI(token)
        user = await api.get_me()
        if not user:
            await message.answer(get_text("token_invalid", lang))
            return
        username = user.get("username", "")
        await save_token(message.from_user.id, token, username)
        await message.answer(get_text("auth_success", lang, username=username))
    except Exception as e:
        await message.answer(get_text("auth_error", lang, e=e))


@router.message(Command("logout"))
async def cmd_logout(message: Message, lang: str):
    await delete_token(message.from_user.id)
    await message.answer(get_text("logged_out", lang))
