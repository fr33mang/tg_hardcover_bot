"""Shared rendering for every book list screen: shelf, list and search results."""

import html
import math
from dataclasses import dataclass, field

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api import is_author
from callbacks import BookDetailCallback, NoopCallback
from i18n import get_text

PAGE_SIZE = 5
BUTTON_MAX = 32


@dataclass
class BookRow:
    id: int
    title: str
    slug: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    my_rating: float | None = None
    progress: tuple[int, int | None] | None = None  # (pages read, total pages or None)


def progress_bar(pages: int, total: int | None, lang: str) -> str:
    if total:
        pct = min(100, round(pages * 100 / total))
        filled = round(pct / 10)
        return f"{'▓' * filled}{'░' * (10 - filled)} {pct}% · " + get_text(
            "progress_pages", lang, pages=pages, total=total
        )
    return get_text("progress_pages_only", lang, pages=pages)


def total_pages(user_book: dict | None, book: dict | None) -> int | None:
    """Pages of the edition the user reads, falling back to the book's default edition."""
    edition = (user_book or {}).get("edition") or {}
    return edition.get("pages") or (book or {}).get("pages")


def _authors(contributions: list[dict] | None) -> list[str]:
    seen: set = set()
    names = []
    for c in contributions or []:
        if not is_author(c):
            continue
        key = c["author"].get("id") or c["author"]["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(c["author"]["name"])
    return names


def row_from_book(
    book: dict, my_rating: float | None = None, progress: tuple[int, int | None] | None = None
) -> BookRow:
    """A row from a GraphQL `book` object (shelf / list items)."""
    return BookRow(
        id=book.get("id"),
        title=book.get("title") or "?",
        slug=book.get("slug") or "",
        authors=_authors(book.get("contributions")),
        year=book.get("release_year"),
        my_rating=my_rating,
        progress=progress,
    )


def row_from_user_book(user_book: dict) -> BookRow:
    """A shelf item: the book plus the user's rating and, for a book in progress, the pages read."""
    book = user_book.get("book") or {}
    reads = user_book.get("user_book_reads") or []
    progress = None
    if reads and reads[0].get("progress_pages"):
        progress = (reads[0]["progress_pages"], total_pages(user_book, book))
    return row_from_book(book, user_book.get("rating"), progress)


def dedup_names(names: list[str] | None) -> list[str]:
    seen: set = set()
    out = []
    for n in names or []:
        key = n.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(n)
    return out


def row_from_search(book: dict) -> BookRow:
    """A row from a normalized search hit (HardcoverAPI.search_books_page)."""
    authors = dedup_names(book.get("authors"))
    return BookRow(
        id=book["id"],
        title=book.get("title") or "?",
        slug=book.get("slug") or "",
        authors=authors,
        year=book.get("release_year"),
    )


def book_url(row_or_book) -> str | None:
    """A stable link by id: Hardcover redirects it to the current slug, which can change over time."""
    book_id = row_or_book.id if isinstance(row_or_book, BookRow) else (row_or_book or {}).get("id")
    return f"https://hardcover.app/id/book/{book_id}" if book_id else None


def format_row(row: BookRow, lang: str) -> str:
    line = f"<b>{html.escape(row.title)}</b>"
    if row.authors:
        shown = ", ".join(html.escape(a) for a in row.authors[:2])
        if len(row.authors) > 2:
            shown += f" {get_text('et_al', lang)}"
        line += f" — {shown}"
    if row.year:
        line += f" ({row.year})"
    if row.my_rating:
        line += f" {'⭐' * int(row.my_rating)}"
    url = book_url(row)
    if url:
        line += f' <a href="{url}">🔗</a>'
    if row.progress:
        line += "\n   " + progress_bar(row.progress[0], row.progress[1], lang)
    return line


def button_label(row: BookRow) -> str:
    """`Title — Surname`, trimmed to fit a Telegram button."""
    label = row.title
    if row.authors:
        surname = row.authors[0].split()[-1]
        label = f"{row.title} — {surname}"
        if len(label) > BUTTON_MAX:
            label = row.title
    if len(label) > BUTTON_MAX:
        label = label[: BUTTON_MAX - 1].rstrip() + "…"
    return label


def build_book_list(
    rows: list[BookRow],
    title: str,
    lang: str,
    *,
    page: int,
    total: int,
    prev_cb: str | None,
    next_cb: str | None,
    bottom: list[InlineKeyboardButton] | None = None,
) -> tuple[str, InlineKeyboardMarkup]:
    pages = max(1, math.ceil(total / PAGE_SIZE)) if total else 0
    header = title
    if pages > 1:
        header += " " + get_text("page_indicator", lang, page=page, pages=pages)
    lines = [header, ""]
    lines += [f"{i}. {format_row(row, lang)}" for i, row in enumerate(rows, 1)]

    builder = InlineKeyboardBuilder()
    for row in rows:
        builder.row(
            InlineKeyboardButton(text=button_label(row), callback_data=BookDetailCallback(book_id=row.id).pack())
        )

    nav = []
    if prev_cb:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=prev_cb))
    if pages > 1:
        nav.append(InlineKeyboardButton(text=f"{page}/{pages}", callback_data=NoopCallback().pack()))
    if next_cb:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=next_cb))
    if nav:
        builder.row(*nav)
    if bottom:
        builder.row(*bottom)
    return "\n".join(lines), builder.as_markup()
