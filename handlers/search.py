from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from api import HardcoverAPI
from db import get_token

router = Router()

STATUS_LABELS = {1: "📚 Хочу", 2: "📖 Читаю", 3: "✅ Прочитал"}
STATUS_NAMES = {1: "want_to_read", 2: "reading", 3: "read"}


class AddBookCallback(CallbackData, prefix="add"):
    book_id: int
    status_id: int


def _format_book(book: dict) -> str:
    title = book.get("title", "?")
    contributors = book.get("cached_contributors") or ""
    year = book.get("release_year") or ""
    author = ""
    if contributors:
        import json
        try:
            contribs = json.loads(contributors) if isinstance(contributors, str) else contributors
            authors = [c.get("name", "") for c in contribs if c.get("role") in ("Author", "author", None, "")]
            author = ", ".join(a for a in authors if a)
        except Exception:
            author = str(contributors)
    parts = [f"<b>{title}</b>"]
    if author:
        parts.append(author)
    if year:
        parts.append(f"({year})")
    return " — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "")


def _build_book_keyboard(book_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status_id, label in STATUS_LABELS.items():
        builder.button(
            text=label,
            callback_data=AddBookCallback(book_id=book_id, status_id=status_id),
        )
    builder.adjust(3)
    return builder.as_markup()


@router.message(Command("search"))
async def cmd_search(message: Message):
    query = message.text.removeprefix("/search").strip()
    if not query:
        await message.answer("Использование: /search <название книги>")
        return
    await _do_search(message, query)


@router.message(F.text & ~F.text.startswith("/"))
async def text_search(message: Message):
    token = await get_token(message.from_user.id)
    if not token:
        return
    await _do_search(message, message.text.strip())


async def _do_search(message: Message, query: str):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("Сначала авторизуйтесь: /token")
        return

    api = HardcoverAPI(token)
    try:
        books = await api.search_books(query)
    except Exception as e:
        await message.answer(f"Ошибка поиска: {e}")
        return

    if not books:
        await message.answer("Книги не найдены.")
        return

    for book in books:
        text = _format_book(book)
        kb = _build_book_keyboard(book["id"])
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(AddBookCallback.filter())
async def add_book_callback(callback: CallbackQuery, callback_data: AddBookCallback):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer("Сначала авторизуйтесь: /token", show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        await api.add_or_update_book(callback_data.book_id, callback_data.status_id)
        label = STATUS_LABELS[callback_data.status_id]
        await callback.answer(f"{label} — добавлено!")
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)


@router.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=1)
        return

    token = await get_token(inline_query.from_user.id)
    if not token:
        await inline_query.answer(
            [],
            cache_time=1,
            switch_pm_text="Авторизуйтесь в боте",
            switch_pm_parameter="start",
        )
        return

    api = HardcoverAPI(token)
    try:
        books = await api.search_books(query, limit=10)
    except Exception:
        await inline_query.answer([], cache_time=1)
        return

    results = []
    for book in books:
        import json
        title = book.get("title", "?")
        slug = book.get("slug", "")
        contributors = book.get("cached_contributors") or ""
        author = ""
        if contributors:
            try:
                contribs = json.loads(contributors) if isinstance(contributors, str) else contributors
                authors = [c.get("name", "") for c in contribs if c.get("role") in ("Author", "author", None, "")]
                author = ", ".join(a for a in authors if a)
            except Exception:
                pass

        description = author or "Hardcover"
        text = f"<b>{title}</b>"
        if author:
            text += f"\n{author}"
        if book.get("release_year"):
            text += f" ({book['release_year']})"
        text += f"\nhttps://hardcover.app/books/{slug}"

        results.append(
            InlineQueryResultArticle(
                id=str(book["id"]),
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=text, parse_mode="HTML"
                ),
            )
        )

    await inline_query.answer(results, cache_time=30)
