from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from api import HardcoverAPI
from db import get_token

router = Router()

STATUS_LABELS = {1: "📚 Хочу", 2: "📖 Читаю", 3: "✅ Прочитал"}


class AddBookCallback(CallbackData, prefix="add"):
    book_id: int
    status_id: int


def _dedup_authors(authors: list[str]) -> list[str]:
    seen = set()
    result = []
    for a in authors:
        key = a.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def _format_book_line(book: dict) -> str:
    title = book.get("title", "?")
    authors = _dedup_authors(book.get("authors") or [])
    year = book.get("release_year") or ""
    slug = book.get("slug", "")
    author = ", ".join(authors) if authors else ""
    url = f"https://hardcover.app/books/{slug}" if slug else None

    title_part = f'<a href="{url}">{title}</a>' if url else f"<b>{title}</b>"
    parts = [title_part]
    if author:
        parts.append(author)
    if year:
        parts.append(f"({year})")
    return " — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "")


def _build_results_message(books: list[dict], query: str) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f'🔍 <b>"{query}"</b>\n']
    for i, book in enumerate(books, 1):
        lines.append(f"{i}. {_format_book_line(book)}")

    builder = InlineKeyboardBuilder()
    for i, book in enumerate(books, 1):
        for status_id, label in STATUS_LABELS.items():
            builder.button(
                text=f"{i}: {label}",
                callback_data=AddBookCallback(book_id=book["id"], status_id=status_id),
            )
        builder.adjust(3)

    return "\n".join(lines), builder.as_markup()


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

    text, kb = _build_results_message(books, query)
    await message.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)


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
        title = book.get("title", "?")
        slug = book.get("slug", "")
        authors = _dedup_authors(book.get("authors") or [])
        author = ", ".join(authors) if authors else ""

        text = f"<b>{title}</b>"
        if author:
            text += f"\n{author}"
        if book.get("release_year"):
            text += f" ({book['release_year']})"
        if slug:
            text += f"\nhttps://hardcover.app/books/{slug}"

        results.append(
            InlineQueryResultArticle(
                id=str(book["id"]),
                title=title,
                description=author or "Hardcover",
                input_message_content=InputTextMessageContent(
                    message_text=text, parse_mode="HTML"
                ),
            )
        )

    await inline_query.answer(results, cache_time=30)
