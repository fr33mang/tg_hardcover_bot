import asyncio
import html
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import HardcoverAPI
from callbacks import (
    AddBookCallback,
    AddToListCallback,
    BackToBookCallback,
    BookDetailCallback,
    CloseMessageCallback,
    DeleteBookCallback,
    ShowListsCallback,
)
from db import get_token
from i18n import get_text

router = Router()

SEARCH_PAGE_SIZE = 5


class SearchPageCallback(CallbackData, prefix="search"):
    query: str
    page: int


def _dedup_authors(authors: list[str]) -> list[str]:
    seen = set()
    result = []
    for a in authors:
        key = a.lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def _book_url(book: dict) -> str | None:
    slug = book.get("slug", "")
    return f"https://hardcover.app/books/{slug}" if slug else None


def _format_book_line(book: dict, lang: str) -> str:
    title = book.get("title", "?")
    authors = _dedup_authors(book.get("authors") or [])
    year = book.get("release_year") or ""
    author = ", ".join(authors) if authors else ""

    url = _book_url(book)
    safe_title = html.escape(title)
    link = f' <a href="{url}">🔗</a>' if url else ""
    if len(authors) > 2:
        author = html.escape(", ".join(authors[:2])) + f" {get_text('et_al', lang)}"
    elif author:
        author = html.escape(author)
    parts = [f"<b>{safe_title}</b>"]
    if author:
        parts.append(author)
    if year:
        parts.append(f"({year})")
    line = " — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "")
    return line + link


def _build_results_message(books: list[dict], query: str, lang: str, page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    lines = [f'🔍 <b>"{html.escape(query)}"</b>\n']
    for i, book in enumerate(books, 1):
        lines.append(f"{i}. {_format_book_line(book, lang)}")
    lines.append(f"\n<i>{get_text('search_hint', lang)}</i>")

    builder = InlineKeyboardBuilder()
    builder.row(
        *[
            InlineKeyboardButton(text=str(i), callback_data=BookDetailCallback(book_id=book["id"]).pack())
            for i, book in enumerate(books, 1)
        ]
    )

    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(text=get_text("btn_prev", lang), callback_data=SearchPageCallback(query=query, page=page - 1).pack())
        )
    if len(books) == SEARCH_PAGE_SIZE:
        nav.append(
            InlineKeyboardButton(text=get_text("btn_next", lang), callback_data=SearchPageCallback(query=query, page=page + 1).pack())
        )
    if nav:
        builder.row(*nav)

    return "\n".join(lines), builder.as_markup()


def _build_book_detail_text(book: dict, lang: str) -> str:
    title = book.get("title", "?")
    authors = _dedup_authors(book.get("authors") or [])
    year = book.get("release_year")
    description = book.get("description") or ""
    rating = book.get("rating")
    ratings_count = book.get("ratings_count")

    safe_title = html.escape(title)
    meta = []
    if authors:
        meta.append(html.escape(", ".join(authors)))
    if year:
        meta.append(str(year))

    lines = [f"<b>{safe_title}</b>"]
    if meta:
        lines.append(" · ".join(meta))
    if rating:
        stars = f"<b>{rating:.1f}</b> ⭐"
        if ratings_count:
            stars += f" ({get_text('ratings_count', lang, count=ratings_count)})"
        lines.append(stars)
    if description:
        desc = html.escape(description.strip())
        if len(desc) > 800:
            desc = desc[:800].rstrip() + "…"
        lines.append(f"\n{desc}")

    return "\n".join(lines)


def _build_book_buttons(
    book_id: int, lang: str, current_status_id: int | None = None, book_url: str | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status_id in range(1, 7):
        label = get_text(f"status_{status_id}_short", lang)
        text = f"● {label}" if status_id == current_status_id else label
        builder.button(text=text, callback_data=AddBookCallback(book_id=book_id, status_id=status_id))
    builder.adjust(3, 3)
    if current_status_id:
        builder.row(
            InlineKeyboardButton(text=get_text("btn_delete_status", lang), callback_data=DeleteBookCallback(book_id=book_id).pack())
        )
    builder.row(InlineKeyboardButton(text=get_text("btn_add_to_list", lang), callback_data=ShowListsCallback(book_id=book_id).pack()))
    if book_url:
        builder.row(InlineKeyboardButton(text=get_text("btn_open_hardcover", lang), url=book_url))
    builder.row(InlineKeyboardButton(text=get_text("btn_close", lang), callback_data=CloseMessageCallback().pack()))
    return builder.as_markup()


def _build_lists_keyboard(book_id: int, lists: list[dict], lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lst in lists:
        list_book_id = lst.get("list_book_id", 0)
        mark = " ✓" if list_book_id else ""
        builder.row(
            InlineKeyboardButton(
                text=f"🔖 {lst['name']} ({lst['books_count']}){mark}",
                callback_data=AddToListCallback(book_id=book_id, list_id=lst["id"], list_book_id=list_book_id).pack(),
            )
        )
    builder.row(InlineKeyboardButton(text=get_text("btn_prev", lang), callback_data=BackToBookCallback(book_id=book_id).pack()))
    return builder.as_markup()


@router.message(Command("search"))
async def cmd_search(message: Message, lang: str):
    query = message.text.removeprefix("/search").strip()
    if not query:
        await message.answer(get_text("search_usage", lang))
        return
    await _do_search(message, query, lang)


@router.message(F.text & ~F.text.startswith("/"))
async def text_search(message: Message, lang: str):
    token = await get_token(message.from_user.id)
    if not token:
        return
    await _do_search(message, message.text.strip(), lang)


async def _do_search(message: Message, query: str, lang: str):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer(get_text("auth_required", lang))
        return

    api = HardcoverAPI(token)
    try:
        books = await api.search_books(query, limit=SEARCH_PAGE_SIZE, page=1)
    except Exception as e:
        await message.answer(get_text("search_error", lang, e=e))
        return

    if not books:
        await message.answer(get_text("no_books_found", lang))
        return

    text, kb = _build_results_message(books, query, lang, page=1)
    await message.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(SearchPageCallback.filter())
async def search_page_callback(callback: CallbackQuery, callback_data: SearchPageCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        books = await api.search_books(callback_data.query, limit=SEARCH_PAGE_SIZE, page=callback_data.page)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return

    if not books:
        await callback.answer(get_text("no_more_results", lang), show_alert=True)
        return

    text, kb = _build_results_message(books, callback_data.query, lang, page=callback_data.page)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(BookDetailCallback.filter())
async def book_detail_callback(callback: CallbackQuery, callback_data: BookDetailCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    await callback.answer()

    api = HardcoverAPI(token)
    try:
        book, user_book = await asyncio.gather(
            api.get_book(callback_data.book_id),
            api.get_user_book(callback_data.book_id),
        )
    except Exception as e:
        await callback.message.answer(get_text("load_error", lang, e=e))
        return

    if not book:
        await callback.message.answer(get_text("book_not_found", lang))
        return

    current_status_id = user_book["status_id"] if user_book else None
    url = _book_url(book)
    text = _build_book_detail_text(book, lang)
    kb = _build_book_buttons(book["id"], lang, current_status_id, book_url=url)
    image_url = book.get("image_url")

    if image_url:
        await callback.message.answer_photo(
            photo=image_url,
            caption=text,
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(AddBookCallback.filter())
async def add_book_callback(callback: CallbackQuery, callback_data: AddBookCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        await api.add_or_update_book(callback_data.book_id, callback_data.status_id)
        book = await api.get_book(callback_data.book_id)
        url = _book_url(book) if book else None
        new_kb = _build_book_buttons(callback_data.book_id, lang, callback_data.status_id, book_url=url)
        try:
            await callback.message.edit_reply_markup(reply_markup=new_kb)
        except Exception as e:
            logging.warning("edit_reply_markup failed: %s", e)
        label = get_text(f"status_{callback_data.status_id}_short", lang)
        await callback.answer(get_text("status_added", lang, label=label))
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)


@router.callback_query(DeleteBookCallback.filter())
async def delete_book_callback(callback: CallbackQuery, callback_data: DeleteBookCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        user_book, book = await asyncio.gather(
            api.get_user_book(callback_data.book_id),
            api.get_book(callback_data.book_id),
        )
        if user_book:
            await api.delete_user_book(user_book["id"])
        url = _book_url(book) if book else None
        new_kb = _build_book_buttons(callback_data.book_id, lang, None, book_url=url)
        try:
            await callback.message.edit_reply_markup(reply_markup=new_kb)
        except Exception as e:
            logging.warning("edit_reply_markup failed: %s", e)
        await callback.answer(get_text("book_deleted", lang))
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)


@router.callback_query(ShowListsCallback.filter())
async def show_lists_callback(callback: CallbackQuery, callback_data: ShowListsCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        lists = await api.get_user_lists(book_id=callback_data.book_id)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return

    if not lists:
        await callback.answer(get_text("no_lists", lang), show_alert=True)
        return

    kb = _build_lists_keyboard(callback_data.book_id, lists, lang)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(AddToListCallback.filter())
async def add_to_list_callback(callback: CallbackQuery, callback_data: AddToListCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        if callback_data.list_book_id:
            await api.remove_book_from_list(callback_data.list_book_id)
            toast = get_text("removed_from_list", lang)
        else:
            await api.add_book_to_list(callback_data.list_id, callback_data.book_id)
            toast = get_text("added_to_list", lang)
        lists = await api.get_user_lists(book_id=callback_data.book_id)
        kb = _build_lists_keyboard(callback_data.book_id, lists, lang)
        await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.answer(toast)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)


@router.callback_query(BackToBookCallback.filter())
async def back_to_book_callback(callback: CallbackQuery, callback_data: BackToBookCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        user_book, book = await asyncio.gather(
            api.get_user_book(callback_data.book_id),
            api.get_book(callback_data.book_id),
        )
        current_status_id = user_book["status_id"] if user_book else None
        url = _book_url(book) if book else None
        kb = _build_book_buttons(callback_data.book_id, lang, current_status_id, book_url=url)
        await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.answer()
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)


@router.callback_query(CloseMessageCallback.filter())
async def close_message_callback(callback: CallbackQuery, lang: str):
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning("delete message failed: %s", e)
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await callback.answer()


@router.inline_query()
async def inline_search(inline_query: InlineQuery, lang: str):
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=1)
        return

    token = await get_token(inline_query.from_user.id)
    if not token:
        await inline_query.answer(
            [],
            cache_time=1,
            switch_pm_text=get_text("inline_auth_prompt", lang),
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
                input_message_content=InputTextMessageContent(message_text=text, parse_mode="HTML"),
            )
        )

    await inline_query.answer(results, cache_time=30)
