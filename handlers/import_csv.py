import asyncio
import csv
import io
import re

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, Document

from api import HardcoverAPI
from db import get_token

router = Router()

GOODREADS_STATUS_MAP = {
    "read": 3,
    "currently-reading": 2,
    "to-read": 1,
}


class ImportStates(StatesGroup):
    waiting_for_file = State()


def _clean_isbn(raw: str) -> str:
    return re.sub(r'[^0-9X]', '', raw.upper())


def _parse_rating(raw: str) -> float | None:
    try:
        r = float(raw)
        return r if r > 0 else None
    except (ValueError, TypeError):
        return None


def _parse_csv(content: bytes) -> list[dict]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({
            "title": row.get("Title", "").strip(),
            "author": row.get("Author", "").strip(),
            "isbn": _clean_isbn(row.get("ISBN", "")),
            "isbn13": _clean_isbn(row.get("ISBN13", "")),
            "rating": _parse_rating(row.get("My Rating", "0")),
            "shelf": row.get("Exclusive Shelf", "read").strip(),
        })
    return rows


@router.message(Command("import"))
async def cmd_import(message: Message, state: FSMContext):
    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("Сначала авторизуйтесь: /token")
        return
    await state.set_state(ImportStates.waiting_for_file)
    await message.answer(
        "Отправьте файл <b>goodreads_library_export.csv</b>\n\n"
        "Экспортировать можно на goodreads.com: My Books → Import/Export → Export Library",
        parse_mode="HTML",
    )


@router.message(ImportStates.waiting_for_file, F.document)
async def process_import_file(message: Message, state: FSMContext):
    await state.clear()
    doc: Document = message.document

    if not doc.file_name.endswith(".csv"):
        await message.answer("Пожалуйста, отправьте файл .csv")
        return

    token = await get_token(message.from_user.id)
    if not token:
        await message.answer("Сначала авторизуйтесь: /token")
        return

    status_msg = await message.answer("⏳ Загружаю файл...")

    bot = message.bot
    file = await bot.get_file(doc.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read()

    rows = _parse_csv(content)
    total = len(rows)
    await status_msg.edit_text(f"📋 Найдено {total} книг. Начинаю импорт...")

    api = HardcoverAPI(token)
    ok = 0
    skipped = 0
    failed = 0
    failed_titles = []

    for i, row in enumerate(rows):
        title = row["title"]
        shelf = row["shelf"]
        status_id = GOODREADS_STATUS_MAP.get(shelf, 3)
        rating = row["rating"]

        if i % 10 == 0:
            try:
                await status_msg.edit_text(
                    f"⏳ Обрабатываю {i}/{total}...\n"
                    f"✅ {ok} добавлено | ⏭ {skipped} пропущено | ❌ {failed} ошибок"
                )
            except Exception:
                pass

        books = []

        for isbn in filter(None, [row["isbn13"], row["isbn"]]):
            try:
                books = await api.search_books_by_isbn(isbn)
            except Exception:
                pass
            if books:
                break

        if not books:
            try:
                books = await api.search_books(title, limit=1)
            except Exception:
                pass

        if not books:
            failed += 1
            failed_titles.append(title)
            await asyncio.sleep(0.5)
            continue

        book_id = books[0]["id"]
        try:
            await api.add_or_update_book(book_id, status_id, rating)
            ok += 1
        except Exception as e:
            if "already" in str(e).lower():
                skipped += 1
            else:
                failed += 1
                failed_titles.append(title)

        await asyncio.sleep(1.1)

    summary = (
        f"✅ Импорт завершён!\n\n"
        f"Добавлено: {ok}\n"
        f"Пропущено: {skipped}\n"
        f"Не найдено: {failed}"
    )
    if failed_titles:
        preview = failed_titles[:10]
        summary += "\n\nНе найдены:\n" + "\n".join(f"• {t}" for t in preview)
        if len(failed_titles) > 10:
            summary += f"\n...и ещё {len(failed_titles) - 10}"

    await status_msg.edit_text(summary)


@router.message(ImportStates.waiting_for_file)
async def import_wrong_message(message: Message):
    await message.answer("Пожалуйста, отправьте файл .csv или /cancel для отмены.")
