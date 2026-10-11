"""Back navigation: re-render the list screen the user came from."""

from aiogram import Router
from aiogram.types import CallbackQuery

from api import HardcoverAPI
from callbacks import BackCallback
from db import get_nav_context, get_token
from handlers.search import render_search
from handlers.shelves import render_library, render_list, render_shelf
from i18n import get_text
from screen import show_screen

router = Router()


@router.callback_query(BackCallback.filter())
async def back_callback(callback: CallbackQuery, lang: str):
    token = await get_token(callback.from_user.id)
    if not token:
        await callback.answer(get_text("auth_required", lang), show_alert=True)
        return

    api = HardcoverAPI(token)
    ctx = await get_nav_context(callback.from_user.id) or {}
    kind = ctx.get("kind")
    try:
        if kind == "shelf":
            screen = await render_shelf(api, lang, ctx["id"], ctx.get("offset", 0))
        elif kind == "list":
            screen = await render_list(api, lang, ctx["id"], ctx.get("offset", 0))
        elif kind == "search":
            screen = await render_search(api, lang, ctx["query"], ctx.get("page", 1))
        else:
            screen = None
        if screen is None:
            screen = await render_library(api, lang)
    except Exception as e:
        await callback.answer(get_text("error_generic", lang, e=e), show_alert=True)
        return

    await show_screen(*screen, callback=callback)
    await callback.answer()
