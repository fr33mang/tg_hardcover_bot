from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import HardcoverAPI
from callbacks import BookDetailCallback
from db import get_token

router = Router()

PAGE_SIZE = 10
STATUS_NAMES = {1: "Хочу прочитать", 2: "Читаю", 3: "Прочитал"}
STATUS_EMOJI = {1: "📚", 2: "📖", 3: "✅"}


class ShelfPageCallback(CallbackData, prefix="shelf"):
    status_id: int
    offset: int


class BackToShelvesCallback(CallbackData, prefix="shelves_back"):
    pass


def _dedup_authors_by_id(contribs: list[dict]) -> list[str]:
    seen_ids = set()
    names = []
    for c in contribs:
        author = c.get("author")
        if not author or c.get("contribution"):
            continue
        aid = author.get("id")
        if aid and aid in seen_ids:
            continue
        if aid:
            seen_ids.add(aid)
        names.append(author["name"])
    return names


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


@router.callback_query(BackToShelvesCallback.filter())
async def back_to_shelves_callback(callback: CallbackQuery):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer("Сначала авторизуйтесь: /token", show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        counts = await api.get_my_shelves()
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
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
    await callback.message.edit_text("Ваши полки:", reply_markup=builder.as_markup())
    await callback.answer()


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

    page = offset // PAGE_SIZE + 1
    lines = [f"{STATUS_EMOJI[status_id]} <b>{STATUS_NAMES[status_id]}</b> (стр. {page})\n"]
    book_ids = []
    for i, ub in enumerate(books, 1):
        book = ub.get("book", {})
        title = book.get("title", "?")
        slug = book.get("slug", "")
        rating = ub.get("rating")
        stars = f" {'⭐' * int(rating)}" if rating else ""
        authors = _dedup_authors_by_id(book.get("contributions") or [])
        if len(authors) > 2:
            author_str = f" — {', '.join(authors[:2])} и др."
        elif authors:
            author_str = f" — {', '.join(authors)}"
        else:
            author_str = ""
        hc_link = f' <a href="https://hardcover.app/books/{slug}">🔗</a>' if slug else ""
        lines.append(f"{i}. <b>{title}</b>{author_str}{stars}{hc_link}")
        book_ids.append(book.get("id"))

    lines.append("\n<i>Нажмите на номер для управления книгой</i>")
    text = "\n".join(lines)

    builder = InlineKeyboardBuilder()

    num_btns = [
        InlineKeyboardButton(text=str(i), callback_data=BookDetailCallback(book_id=bid).pack())
        for i, bid in enumerate(book_ids, 1)
    ]
    for i in range(0, len(num_btns), 5):
        builder.row(*num_btns[i:i + 5])

    nav_btns = []
    if offset > 0:
        nav_btns.append(InlineKeyboardButton(
            text="← Назад",
            callback_data=ShelfPageCallback(status_id=status_id, offset=offset - PAGE_SIZE).pack(),
        ))
    if len(books) == PAGE_SIZE:
        nav_btns.append(InlineKeyboardButton(
            text="Вперёд →",
            callback_data=ShelfPageCallback(status_id=status_id, offset=offset + PAGE_SIZE).pack(),
        ))
    if nav_btns:
        builder.row(*nav_btns)

    builder.row(InlineKeyboardButton(text="📋 Все полки", callback_data=BackToShelvesCallback().pack()))

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup(), disable_web_page_preview=True)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup(), disable_web_page_preview=True)
    await callback.answer()
