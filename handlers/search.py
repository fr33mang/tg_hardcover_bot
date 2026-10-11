import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from api import HardcoverAPI
from db import get_nav_context, get_token, set_nav_context
from i18n import get_text
from screen import show_screen
from views import PAGE_SIZE, build_book_list, dedup_names, row_from_search

router = Router()


class SearchPageCallback(CallbackData, prefix="search"):
    page: int  # the query lives in nav_context: callback_data is capped at 64 bytes


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


async def render_search(api: HardcoverAPI, lang: str, query: str, page: int) -> tuple[str, InlineKeyboardMarkup] | None:
    books, total = await api.search_books_page(query, limit=PAGE_SIZE, page=page)
    if not books:
        return None
    rows = [row_from_search(b) for b in books]
    title = f'🔍 <b>"{html.escape(query)}"</b>'
    prev_cb = SearchPageCallback(page=page - 1).pack() if page > 1 else None
    next_cb = SearchPageCallback(page=page + 1).pack() if page * PAGE_SIZE < total else None
    return build_book_list(rows, title, lang, page=page, total=total, prev_cb=prev_cb, next_cb=next_cb)


async def _do_search(message: Message, query: str, lang: str):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer(get_text("auth_required", lang))
        return

    api = HardcoverAPI(token)
    try:
        screen = await render_search(api, lang, query, page=1)
    except Exception as e:
        await message.answer(get_text("search_error", lang, e=e))
        return

    if screen is None:
        await message.answer(get_text("no_books_found", lang))
        return

    await set_nav_context(message.from_user.id, {"kind": "search", "query": query, "page": 1})
    await show_screen(*screen, message=message)


@router.callback_query(SearchPageCallback.filter())
async def search_page_callback(callback: CallbackQuery, callback_data: SearchPageCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    ctx = await get_nav_context(callback.from_user.id)
    if not ctx or ctx.get("kind") != "search":
        await callback.answer(get_text("search_expired", lang), show_alert=True)
        return
    query = ctx["query"]

    api = HardcoverAPI(token)
    try:
        screen = await render_search(api, lang, query, page=callback_data.page)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return

    if screen is None:
        await callback.answer(get_text("no_more_results", lang), show_alert=True)
        return

    await set_nav_context(callback.from_user.id, {"kind": "search", "query": query, "page": callback_data.page})
    await show_screen(*screen, callback=callback)
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
        authors = dedup_names(book.get("authors"))
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
