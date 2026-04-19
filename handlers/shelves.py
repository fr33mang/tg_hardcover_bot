from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import HardcoverAPI
from db import get_token

router = Router()

PAGE_SIZE = 10
STATUS_NAMES = {1: "Хочу прочитать", 2: "Читаю", 3: "Прочитал"}
STATUS_EMOJI = {1: "📚", 2: "📖", 3: "✅"}


class ShelfPageCallback(CallbackData, prefix="shelf"):
    status_id: int
    offset: int


@router.message(Command("shelves"))
async def cmd_shelves(message: Message):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("Сначала авторизуйтесь: /token")
        return

    api = HardcoverAPI(token)
    try:
        counts = await api.get_my_shelves()
    except Exception as e:
        await message.answer(f"Ошибка загрузки полок: {e}")
        return

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"📚 Хочу прочитать ({counts['want_to_read']})",
        callback_data=ShelfPageCallback(status_id=1, offset=0),
    )
    builder.button(
        text=f"📖 Читаю ({counts['reading']})",
        callback_data=ShelfPageCallback(status_id=2, offset=0),
    )
    builder.button(
        text=f"✅ Прочитал ({counts['read']})",
        callback_data=ShelfPageCallback(status_id=3, offset=0),
    )
    builder.adjust(1)
    await message.answer("Ваши полки:", reply_markup=builder.as_markup())


@router.callback_query(ShelfPageCallback.filter())
async def shelf_page_callback(callback: CallbackQuery, callback_data: ShelfPageCallback):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer("Сначала авторизуйтесь: /token", show_alert=True)
        return

    api = HardcoverAPI(token)
    status_id = callback_data.status_id
    offset = callback_data.offset

    try:
        books = await api.get_shelf_books(status_id, limit=PAGE_SIZE, offset=offset)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return

    if not books:
        await callback.answer("Полка пуста.", show_alert=True)
        return

    lines = [f"{STATUS_EMOJI[status_id]} <b>{STATUS_NAMES[status_id]}</b> (стр. {offset // PAGE_SIZE + 1})\n"]
    for ub in books:
        book = ub.get("book", {})
        title = book.get("title", "?")
        rating = ub.get("rating")
        stars = f" {'⭐' * int(rating)}" if rating else ""
        lines.append(f"• {title}{stars}")

    text = "\n".join(lines)

    builder = InlineKeyboardBuilder()
    if offset > 0:
        builder.button(
            text="← Назад",
            callback_data=ShelfPageCallback(status_id=status_id, offset=offset - PAGE_SIZE),
        )
    if len(books) == PAGE_SIZE:
        builder.button(
            text="Вперёд →",
            callback_data=ShelfPageCallback(status_id=status_id, offset=offset + PAGE_SIZE),
        )
    builder.adjust(2)

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()
