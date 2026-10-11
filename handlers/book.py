"""The book card and its sub-panels (more statuses, rating, lists, full description).

Every tap performs its action and then re-renders the whole card through render_card, so
the text (status line, rating) and the keyboard never drift apart.
"""

import asyncio
import html
import logging
import time

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import HardcoverAPI
from callbacks import (
    AddBookCallback,
    AddToListCallback,
    BackCallback,
    BackToBookCallback,
    BookDetailCallback,
    CardPanelCallback,
    CloseMessageCallback,
    DeleteBookCallback,
    RateCallback,
    ShowListsCallback,
)
from db import get_token
from i18n import get_text
from screen import show_screen
from views import book_url, dedup_names

router = Router()

STATUS_READ = 3
PRIMARY_STATUSES = (1, 2, 3)
OTHER_STATUSES = (4, 5, 6)
DESC_SHORT = 500
DESC_FULL = 3000

# get_book is static catalog data; cache it briefly so a few taps on one card cost one request
_BOOK_TTL = 300
_book_cache: dict[int, tuple[float, dict]] = {}


async def _get_book(api: HardcoverAPI, book_id: int) -> dict | None:
    hit = _book_cache.get(book_id)
    if hit and time.monotonic() - hit[0] < _BOOK_TTL:
        return hit[1]
    book = await api.get_book(book_id)
    if book:
        _book_cache[book_id] = (time.monotonic(), book)
    return book


def _fmt_rating(value: float) -> str:
    return f"{value:g}"


def _card_text(book: dict, user_book: dict | None, lang: str, full_desc: bool) -> str:
    lines = [f"<b>{html.escape(book.get('title') or '?')}</b>"]

    meta = []
    authors = dedup_names(book.get("authors"))
    if authors:
        meta.append(html.escape(", ".join(authors)))
    if book.get("release_year"):
        meta.append(str(book["release_year"]))
    if book.get("pages"):
        meta.append(get_text("pages_short", lang, pages=book["pages"]))
    if meta:
        lines.append(" · ".join(meta))

    facts = []
    if book.get("rating"):
        hc = f"⭐ <b>{book['rating']:.1f}</b>"
        if book.get("ratings_count"):
            hc += f" · {get_text('ratings_count', lang, count=f'{book['ratings_count']:,}'.replace(',', ' '))}"
        facts.append(hc)
    series = book.get("series")
    if series:
        label = html.escape(series["name"])
        if series.get("position") is not None:
            label += f" #{series['position']}"
        facts.append(label)
    if facts:
        lines.append(" · ".join(facts))

    lines.append("")
    if user_book:
        state = get_text(f"status_{user_book['status_id']}", lang)
        if user_book.get("rating"):
            state += f" · {get_text('my_rating', lang)} ⭐ {_fmt_rating(user_book['rating'])}"
    else:
        state = get_text("not_on_shelf", lang)
    lines.append(f"<i>{state}</i>")

    description = (book.get("description") or "").strip()
    if description:
        limit = DESC_FULL if full_desc else DESC_SHORT
        desc = html.escape(description)
        if len(desc) > limit:
            desc = desc[:limit].rstrip() + "…"
        lines += ["", desc]
    return "\n".join(lines)


def _description_truncated(book: dict) -> bool:
    return len((book.get("description") or "").strip()) > DESC_SHORT


def _status_button(book_id: int, status_id: int, current: int | None, lang: str) -> InlineKeyboardButton:
    label = get_text(f"status_{status_id}_short", lang)
    if status_id == current:
        label = f"● {label}"
    return InlineKeyboardButton(text=label, callback_data=AddBookCallback(book_id=book_id, status_id=status_id).pack())


def _to_book_button(book_id: int, lang: str, key: str = "btn_to_book") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=get_text(key, lang), callback_data=BackToBookCallback(book_id=book_id).pack())


def _main_keyboard(book: dict, user_book: dict | None, lang: str) -> InlineKeyboardMarkup:
    book_id = book["id"]
    current = user_book["status_id"] if user_book else None
    b = InlineKeyboardBuilder()
    b.row(*[_status_button(book_id, s, current, lang) for s in PRIMARY_STATUSES])
    b.row(
        InlineKeyboardButton(
            text=get_text("btn_rate", lang), callback_data=CardPanelCallback(book_id=book_id, panel="rate").pack()
        ),
        InlineKeyboardButton(
            text=get_text("btn_add_to_list", lang), callback_data=ShowListsCallback(book_id=book_id).pack()
        ),
        InlineKeyboardButton(
            text=get_text("btn_more", lang), callback_data=CardPanelCallback(book_id=book_id, panel="more").pack()
        ),
    )
    bottom = []
    url = book_url(book)
    if url:
        bottom.append(InlineKeyboardButton(text=get_text("btn_open_hardcover", lang), url=url))
    bottom.append(InlineKeyboardButton(text=get_text("btn_back", lang), callback_data=BackCallback().pack()))
    b.row(*bottom)
    return b.as_markup()


def _more_keyboard(book: dict, user_book: dict | None, lang: str, full_desc: bool) -> InlineKeyboardMarkup:
    book_id = book["id"]
    current = user_book["status_id"] if user_book else None
    b = InlineKeyboardBuilder()
    b.row(*[_status_button(book_id, s, current, lang) for s in OTHER_STATUSES])
    if _description_truncated(book):
        key, panel = ("btn_short_desc", "main") if full_desc else ("btn_full_desc", "desc")
        b.row(
            InlineKeyboardButton(
                text=get_text(key, lang), callback_data=CardPanelCallback(book_id=book_id, panel=panel).pack()
            )
        )
    if user_book:
        b.row(
            InlineKeyboardButton(
                text=get_text("btn_delete_status", lang), callback_data=DeleteBookCallback(book_id=book_id).pack()
            )
        )
    b.row(_to_book_button(book_id, lang))
    return b.as_markup()


def _rate_keyboard(book: dict, user_book: dict | None, lang: str, after_read: bool) -> InlineKeyboardMarkup:
    book_id = book["id"]
    current_half = int(((user_book or {}).get("rating") or 0) * 2)

    def star(half: int) -> InlineKeyboardButton:
        label = _fmt_rating(half / 2)
        if half == current_half:
            label = f"● {label}"
        return InlineKeyboardButton(text=label, callback_data=RateCallback(book_id=book_id, half=half).pack())

    b = InlineKeyboardBuilder()
    b.row(*[star(h) for h in (2, 4, 6, 8, 10)])
    b.row(*[star(h) for h in (3, 5, 7, 9)])
    if current_half:
        b.row(
            InlineKeyboardButton(
                text=get_text("btn_remove_rating", lang), callback_data=RateCallback(book_id=book_id, half=0).pack()
            )
        )
    b.row(_to_book_button(book_id, lang, "btn_skip" if after_read else "btn_to_book"))
    return b.as_markup()


def _lists_keyboard(book_id: int, lists: list[dict], lang: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for lst in lists:
        list_book_id = lst.get("list_book_id", 0)
        mark = " ✓" if list_book_id else ""
        b.row(
            InlineKeyboardButton(
                text=f"🔖 {lst['name']} ({lst['books_count']}){mark}",
                callback_data=AddToListCallback(book_id=book_id, list_id=lst["id"], list_book_id=list_book_id).pack(),
            )
        )
    b.row(_to_book_button(book_id, lang))
    return b.as_markup()


async def render_card(
    api: HardcoverAPI, book_id: int, lang: str, *, panel: str = "main", after_read: bool = False
) -> tuple[str, InlineKeyboardMarkup, str | None] | None:
    """(text, keyboard, cover_url) for the card with the given sub-panel; None if the book is unknown."""
    book, user_book = await asyncio.gather(_get_book(api, book_id), api.get_user_book(book_id))
    if not book:
        return None
    full_desc = panel == "desc"
    text = _card_text(book, user_book, lang, full_desc)
    if panel == "more":
        kb = _more_keyboard(book, user_book, lang, full_desc=False)
    elif panel == "rate":
        kb = _rate_keyboard(book, user_book, lang, after_read)
    elif panel == "lists":
        lists = await api.get_user_lists(book_id=book_id)
        kb = _lists_keyboard(book_id, lists, lang) if lists else _main_keyboard(book, user_book, lang)
    elif panel == "desc":
        kb = _more_keyboard(book, user_book, lang, full_desc=True)
    else:
        kb = _main_keyboard(book, user_book, lang)
    return text, kb, book.get("image_url")


async def _show_card(callback: CallbackQuery, api: HardcoverAPI, book_id: int, lang: str, **kw) -> bool:
    card = await render_card(api, book_id, lang, **kw)
    if card is None:
        await callback.answer(get_text("book_not_found", lang), show_alert=True)
        return False
    text, kb, cover = card
    await show_screen(text, kb, callback=callback, cover_url=cover)
    return True


async def _api_for(callback: CallbackQuery, lang: str) -> HardcoverAPI | None:
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return None
    return HardcoverAPI(token)


@router.callback_query(BookDetailCallback.filter())
async def open_card(callback: CallbackQuery, callback_data: BookDetailCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    try:
        await _show_card(callback, api, callback_data.book_id, lang)
    except Exception as e:
        await callback.answer(get_text("load_error", lang, e=e), show_alert=True)
        return
    await callback.answer()


@router.callback_query(BackToBookCallback.filter())
async def back_to_card(callback: CallbackQuery, callback_data: BackToBookCallback, lang: str):
    await open_card(callback, callback_data, lang)


@router.callback_query(CardPanelCallback.filter())
async def switch_panel(callback: CallbackQuery, callback_data: CardPanelCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    try:
        await _show_card(callback, api, callback_data.book_id, lang, panel=callback_data.panel)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await callback.answer()


@router.callback_query(ShowListsCallback.filter())
async def show_lists(callback: CallbackQuery, callback_data: ShowListsCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    try:
        lists = await api.get_user_lists(book_id=callback_data.book_id)
        if not lists:
            await callback.answer(get_text("no_lists", lang), show_alert=True)
            return
        await _show_card(callback, api, callback_data.book_id, lang, panel="lists")
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await callback.answer()


@router.callback_query(AddToListCallback.filter())
async def toggle_list(callback: CallbackQuery, callback_data: AddToListCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    try:
        if callback_data.list_book_id:
            await api.remove_book_from_list(callback_data.list_book_id)
            toast = get_text("removed_from_list", lang)
        else:
            await api.add_book_to_list(callback_data.list_id, callback_data.book_id)
            toast = get_text("added_to_list", lang)
        await _show_card(callback, api, callback_data.book_id, lang, panel="lists")
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await callback.answer(toast)


@router.callback_query(AddBookCallback.filter())
async def set_status(callback: CallbackQuery, callback_data: AddBookCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    try:
        await api.add_or_update_book(callback_data.book_id, callback_data.status_id)
        # finishing a book is the natural moment to rate it: offer the stars right away
        panel = "rate" if callback_data.status_id == STATUS_READ else "main"
        await _show_card(callback, api, callback_data.book_id, lang, panel=panel, after_read=panel == "rate")
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await callback.answer(
        get_text("status_added", lang, label=get_text(f"status_{callback_data.status_id}_short", lang))
    )


@router.callback_query(DeleteBookCallback.filter())
async def remove_from_shelf(callback: CallbackQuery, callback_data: DeleteBookCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    try:
        user_book = await api.get_user_book(callback_data.book_id)
        if user_book:
            await api.delete_user_book(user_book["id"])
        await _show_card(callback, api, callback_data.book_id, lang)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await callback.answer(get_text("book_deleted", lang))


@router.callback_query(RateCallback.filter())
async def rate(callback: CallbackQuery, callback_data: RateCallback, lang: str):
    api = await _api_for(callback, lang)
    if not api:
        return
    rating = callback_data.half / 2 if callback_data.half else None
    try:
        user_book = await api.get_user_book(callback_data.book_id)
        if user_book:
            await api.rate_book(user_book["id"], rating)
        elif rating is not None:
            # rating a book that is not on a shelf marks it as read, like Hardcover does
            await api.add_or_update_book(callback_data.book_id, STATUS_READ, rating)
        await _show_card(callback, api, callback_data.book_id, lang, panel="rate")
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    toast = get_text("rated_toast", lang, rating=_fmt_rating(rating)) if rating else get_text("rating_removed", lang)
    await callback.answer(toast)


@router.callback_query(CloseMessageCallback.filter())
async def close_message(callback: CallbackQuery, lang: str):
    """Legacy cards from before the single-screen UI still carry a Close button."""
    try:
        await callback.message.delete()
    except Exception as e:
        logging.warning("delete message failed: %s", e)
    await callback.answer()
