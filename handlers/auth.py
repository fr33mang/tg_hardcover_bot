from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from api import HardcoverAPI
from db import save_token, delete_token, get_token

router = Router()


class AuthStates(StatesGroup):
    waiting_for_token = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    has_token = await get_token(message.from_user.id)
    if has_token:
        await message.answer(
            "Вы уже авторизованы. Используйте /shelves, /search или /import."
        )
        return
    await message.answer(
        "👋 Привет! Это бот для Hardcover.\n\n"
        "Чтобы начать:\n"
        "1. Войдите на <a href='https://hardcover.app'>hardcover.app</a>\n"
        "2. Перейдите в Settings → Account → API Token\n"
        "3. Скопируйте токен и отправьте /token\n\n"
        "После авторизации доступны команды:\n"
        "/shelves — ваши полки\n"
        "/search — поиск книг\n"
        "/import — импорт из Goodreads CSV",
        parse_mode="HTML",
    )


@router.message(Command("token"))
async def cmd_token(message: Message, state: FSMContext):
    await state.set_state(AuthStates.waiting_for_token)
    await message.answer(
        "Отправьте ваш Bearer токен с Hardcover.\n"
        "Найти его можно в Settings → Account → API Token на hardcover.app\n\n"
        "<i>Сообщение с токеном будет удалено для безопасности.</i>",
        parse_mode="HTML",
    )


@router.message(AuthStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    await state.clear()
    token = message.text.strip()

    try:
        await message.delete()
    except Exception:
        pass

    if not token:
        await message.answer("Токен не может быть пустым. Попробуйте /token ещё раз.")
        return

    try:
        api = HardcoverAPI(token)
        user = await api.get_me()
        if not user:
            await message.answer("Токен недействителен. Проверьте и попробуйте /token снова.")
            return
        username = user.get("username", "")
        await save_token(message.from_user.id, token, username)
        await message.answer(
            f"✅ Авторизован как @{username}\n\n"
            "Теперь доступны:\n"
            "/shelves — ваши полки\n"
            "/search — поиск книг\n"
            "/import — импорт из Goodreads CSV"
        )
    except Exception as e:
        await message.answer(f"Ошибка авторизации: {e}\nПопробуйте /token снова.")


@router.message(Command("logout"))
async def cmd_logout(message: Message):
    await delete_token(message.from_user.id)
    await message.answer("Вы вышли из аккаунта. Используйте /token для повторной авторизации.")
