"""One message = one screen.

Every navigable view in the bot is rendered into a single "screen" message per chat.
Inline-button taps edit that message in place; a reply-keyboard tap or a typed query
starts a fresh screen message and cleans up the previous one, so the chat never fills
up with dead cards.

Covers are shown as a link preview above the text instead of a photo message, so the
screen stays a text message and can always be edited into any other screen.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
)

from db import get_screen_message, set_screen_message


def _preview(cover_url: str | None) -> LinkPreviewOptions:
    if cover_url:
        return LinkPreviewOptions(url=cover_url, prefer_large_media=True, show_above_text=True)
    return LinkPreviewOptions(is_disabled=True)


async def show_screen(
    text: str,
    kb: InlineKeyboardMarkup | None,
    *,
    message: Message | None = None,
    callback: CallbackQuery | None = None,
    cover_url: str | None = None,
) -> None:
    """Render a screen.

    Pass ``callback`` to edit the tapped message in place, or ``message`` (the user's
    own message) to open a new screen below it. Exactly one of them is required.
    """
    if callback is not None and isinstance(callback.message, Message):
        current = callback.message
        try:
            await current.edit_text(text, reply_markup=kb, link_preview_options=_preview(cover_url))
            await set_screen_message(callback.from_user.id, current.message_id)
            return
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                return
            # e.g. a legacy photo card: can't be edited into text, replace it instead
            logging.info("edit_text failed, replacing screen: %s", e)
        bot, chat_id, user_id = callback.bot, current.chat.id, callback.from_user.id
        await _cleanup(bot, chat_id, current.message_id)
    elif callback is not None:  # inaccessible message: can't edit, open a fresh screen
        bot, chat_id, user_id = callback.bot, callback.from_user.id, callback.from_user.id
        old_id = await get_screen_message(user_id)
        if old_id:
            await _cleanup(bot, chat_id, old_id)
    else:
        bot, chat_id, user_id = message.bot, message.chat.id, message.from_user.id
        old_id = await get_screen_message(user_id)
        if old_id:
            await _cleanup(bot, chat_id, old_id)

    sent = await bot.send_message(chat_id, text, reply_markup=kb, link_preview_options=_preview(cover_url))
    await set_screen_message(user_id, sent.message_id)


async def _cleanup(bot: Bot, chat_id: int, message_id: int) -> None:
    """Remove an old screen; if it can't be deleted (older than 48h), at least drop its buttons."""
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        try:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        except Exception:
            pass
