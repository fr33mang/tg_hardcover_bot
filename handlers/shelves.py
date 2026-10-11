from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import HardcoverAPI
from db import get_token, set_nav_context
from i18n import get_text
from screen import show_screen
from views import PAGE_SIZE, build_book_list, row_from_book, row_from_user_book

router = Router()

STATUS_IDS = [1, 2, 3, 4, 5, 6]


class ShelfPageCallback(CallbackData, prefix="shelf"):
    status_id: int
    offset: int


class ListPageCallback(CallbackData, prefix="lstpage"):
    list_id: int
    offset: int


class BackToLibraryCallback(CallbackData, prefix="lib_back"):
    pass


async def render_library(api: HardcoverAPI, lang: str) -> tuple[str, any]:
    data = await api.get_my_shelves()
    counts = data["counts"]
    lists = data["lists"]

    builder = InlineKeyboardBuilder()

    for status_id in STATUS_IDS:
        count = counts.get(status_id, 0)
        if count > 0:
            label = get_text(f"status_{status_id}", lang)
            builder.row(
                InlineKeyboardButton(
                    text=f"{label} ({count})",
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

    return get_text("library_title", lang), builder.as_markup()


@router.message(Command("library", "shelves"))
async def cmd_library(message: Message, lang: str):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer(get_text("auth_required", lang))
        return
    api = HardcoverAPI(token)
    try:
        text, kb = await render_library(api, lang)
    except Exception as e:
        await message.answer(get_text("error_generic", lang, e=e))
        return
    await set_nav_context(message.from_user.id, None)
    await show_screen(text, kb, message=message)


@router.callback_query(BackToLibraryCallback.filter())
async def back_to_library_callback(callback: CallbackQuery, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return
    api = HardcoverAPI(token)
    try:
        text, kb = await render_library(api, lang)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    await set_nav_context(callback.from_user.id, None)
    await show_screen(text, kb, callback=callback)
    await callback.answer()


def _library_button(lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=get_text("btn_library", lang), callback_data=BackToLibraryCallback().pack())


async def render_shelf(api: HardcoverAPI, lang: str, status_id: int, offset: int) -> tuple[str, any] | None:
    items, total = await api.get_shelf_books(status_id, limit=PAGE_SIZE, offset=offset)
    if not items:
        return None
    rows = [row_from_user_book(ub) for ub in items]
    title = f"<b>{get_text(f'status_{status_id}', lang)}</b>"
    prev_cb = ShelfPageCallback(status_id=status_id, offset=offset - PAGE_SIZE).pack() if offset > 0 else None
    next_cb = (
        ShelfPageCallback(status_id=status_id, offset=offset + PAGE_SIZE).pack() if offset + PAGE_SIZE < total else None
    )
    return build_book_list(
        rows,
        title,
        lang,
        page=offset // PAGE_SIZE + 1,
        total=total,
        prev_cb=prev_cb,
        next_cb=next_cb,
        bottom=[_library_button(lang)],
    )


@router.callback_query(ShelfPageCallback.filter())
async def shelf_page_callback(callback: CallbackQuery, callback_data: ShelfPageCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        screen = await render_shelf(api, lang, callback_data.status_id, callback_data.offset)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    if screen is None:
        await callback.answer(get_text("list_empty", lang), show_alert=True)
        return

    await set_nav_context(
        callback.from_user.id, {"kind": "shelf", "id": callback_data.status_id, "offset": callback_data.offset}
    )
    await show_screen(*screen, callback=callback)
    await callback.answer()


async def render_list(api: HardcoverAPI, lang: str, list_id: int, offset: int) -> tuple[str, any] | None:
    result = await api.get_list_books(list_id, limit=PAGE_SIZE, offset=offset)
    items = result["books"] if result else []
    if not items:
        return None
    total = result["total"]
    rows = [row_from_book(lb.get("book") or {}) for lb in items]
    title = f"🔖 <b>{result['name']}</b>"
    prev_cb = ListPageCallback(list_id=list_id, offset=offset - PAGE_SIZE).pack() if offset > 0 else None
    next_cb = (
        ListPageCallback(list_id=list_id, offset=offset + PAGE_SIZE).pack() if offset + PAGE_SIZE < total else None
    )
    return build_book_list(
        rows,
        title,
        lang,
        page=offset // PAGE_SIZE + 1,
        total=total,
        prev_cb=prev_cb,
        next_cb=next_cb,
        bottom=[_library_button(lang)],
    )


@router.callback_query(ListPageCallback.filter())
async def list_page_callback(callback: CallbackQuery, callback_data: ListPageCallback, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    try:
        screen = await render_list(api, lang, callback_data.list_id, callback_data.offset)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return
    if screen is None:
        await callback.answer(get_text("list_empty", lang), show_alert=True)
        return

    await set_nav_context(
        callback.from_user.id, {"kind": "list", "id": callback_data.list_id, "offset": callback_data.offset}
    )
    await show_screen(*screen, callback=callback)
    await callback.answer()
