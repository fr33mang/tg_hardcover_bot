from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import HardcoverAPI
from callbacks import BookDetailCallback
from db import get_token

router = Router()

PAGE_SIZE = 10

STATUS_LABELS = {
    1: ("📚", "Хочу прочитать"),
    2: ("📖", "Читаю"),
    3: ("✅", "Прочитал"),
    4: ("⏸", "Пауза"),
    5: ("❌", "Не закончил"),
    6: ("🙈", "Игнор"),
}


class ShelfPageCallback(CallbackData, prefix="shelf"):
    status_id: int
    offset: int


class ListPageCallback(CallbackData, prefix="lstpage"):
    list_id: int
    offset: int


class BackToLibraryCallback(CallbackData, prefix="lib_back"):
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


def _format_book_row(book: dict, rating=None) -> str:
    title = book.get("title", "?")
    slug = book.get("slug", "")
    authors = _dedup_authors_by_id(book.get("contributions") or [])
    if len(authors) > 2:
        author_str = f" — {', '.join(authors[:2])} и др."
    elif authors:
        author_str = f" — {', '.join(authors)}"
    else:
        author_str = ""
    stars = f" {'⭐' * int(rating)}" if rating else ""
    hc_link = f' <a href="https://hardcover.app/books/{slug}">🔗</a>' if slug else ""
    return f"<b>{title}</b>{author_str}{stars}{hc_link}"


async def _send_library(api: HardcoverAPI, message: Message = None, callback: CallbackQuery = None):
    data = await api.get_my_shelves()
    counts = data["counts"]
    lists = data["lists"]

    builder = InlineKeyboardBuilder()

    for status_id, (emoji, name) in STATUS_LABELS.items():
        count = counts.get(status_id, 0)
        if count > 0:
            builder.row(
                InlineKeyboardButton(
                    text=f"{emoji} {name} ({count})",
                    callback_data=ShelfPageCallback(status_id=status_id, offset=0).pack(),
                )
            )

    for lst in lists:
        builder.row(
            InlineKeyboardButton(
                text=f"🔖 {lst['name']} ({lst['books_count']})",
                callback_data=ListPageCallback(list_id=lst["id"], offset=0).pack(),
            )
        )

    text = "📖 <b>Библиотека</b>"
    kb = builder.as_markup()

    if message:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await callback.answer()


@router.message(Command("library", "shelves"))
async def cmd_library(message: Message):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("Сначала авторизуйтесь: /token")
        return
    api = HardcoverAPI(token)
    try:
        await _send_library(api, message=message)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.callback_query(BackToLibraryCallback.filter())
async def back_to_library_callback(callback: CallbackQuery):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer("Сначала авторизуйтесь: /token", show_alert=True)
        return
    api = HardcoverAPI(token)
    try:
        await _send_library(api, callback=callback)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)


def _build_book_list(
    items: list[dict], title: str, offset: int, back_cb: str, prev_cb: str | None, next_cb: str | None
) -> tuple[str, any]:
    page = offset // PAGE_SIZE + 1
    lines = [f"{title} (стр. {page})\n"]
    book_ids = []

    for i, item in enumerate(items, 1):
        book = item.get("book", {})
        rating = item.get("rating")
        lines.append(f"{i}. {_format_book_row(book, rating)}")
        book_ids.append(book.get("id"))

    lines.append("\n<i>Нажмите на номер для управления книгой</i>")

    builder = InlineKeyboardBuilder()
    num_btns = [
        InlineKeyboardButton(text=str(i), callback_data=BookDetailCallback(book_id=bid).pack())
        for i, bid in enumerate(book_ids, 1)
    ]
    for i in range(0, len(num_btns), 5):
        builder.row(*num_btns[i : i + 5])

    nav_btns = []
    if prev_cb:
        nav_btns.append(InlineKeyboardButton(text="← Назад", callback_data=prev_cb))
    if next_cb:
        nav_btns.append(InlineKeyboardButton(text="Вперёд →", callback_data=next_cb))
    if nav_btns:
        builder.row(*nav_btns)

    builder.row(InlineKeyboardButton(text="📖 Библиотека", callback_data=back_cb))

    return "\n".join(lines), builder.as_markup()


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
        await callback.answer("Список пуст.", show_alert=True)
        return

    emoji, name = STATUS_LABELS[status_id]
    title = f"{emoji} <b>{name}</b>"
    prev_cb = ShelfPageCallback(status_id=status_id, offset=offset - PAGE_SIZE).pack() if offset > 0 else None
    next_cb = (
        ShelfPageCallback(status_id=status_id, offset=offset + PAGE_SIZE).pack() if len(books) == PAGE_SIZE else None
    )
    back_cb = BackToLibraryCallback().pack()

    text, kb = _build_book_list(books, title, offset, back_cb, prev_cb, next_cb)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(ListPageCallback.filter())
async def list_page_callback(callback: CallbackQuery, callback_data: ListPageCallback):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer("Сначала авторизуйтесь: /token", show_alert=True)
        return

    api = HardcoverAPI(token)
    list_id = callback_data.list_id
    offset = callback_data.offset

    try:
        result = await api.get_list_books(list_id, limit=PAGE_SIZE, offset=offset)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)
        return

    books = result.get("books", [])
    if not books:
        await callback.answer("Список пуст.", show_alert=True)
        return

    title = f"🔖 <b>{result['name']}</b>"
    prev_cb = ListPageCallback(list_id=list_id, offset=offset - PAGE_SIZE).pack() if offset > 0 else None
    next_cb = ListPageCallback(list_id=list_id, offset=offset + PAGE_SIZE).pack() if len(books) == PAGE_SIZE else None
    back_cb = BackToLibraryCallback().pack()

    text, kb = _build_book_list(books, title, offset, back_cb, prev_cb, next_cb)
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()
