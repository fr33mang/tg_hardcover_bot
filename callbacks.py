from aiogram.filters.callback_data import CallbackData


class BookDetailCallback(CallbackData, prefix="book"):
    book_id: int


class AddBookCallback(CallbackData, prefix="add"):
    book_id: int
    status_id: int


class DeleteBookCallback(CallbackData, prefix="del"):
    book_id: int


class ShowListsCallback(CallbackData, prefix="lists"):
    book_id: int


class AddToListCallback(CallbackData, prefix="list_add"):
    book_id: int
    list_id: int
    list_book_id: int  # 0 if not in list


class BackToBookCallback(CallbackData, prefix="back_book"):
    book_id: int


class CloseMessageCallback(CallbackData, prefix="close"):
    pass


class BackCallback(CallbackData, prefix="back"):
    """Return to the list the user came from (stored in nav_context)."""


class MoreCallback(CallbackData, prefix="more"):
    """An item on the settings screen: language | import | token | logout."""

    action: str


class NoopCallback(CallbackData, prefix="noop"):
    """A button that is only a label (e.g. the page indicator)."""


class CardPanelCallback(CallbackData, prefix="panel"):
    """Switch the card's keyboard: main | more | rate | desc (full description)."""

    book_id: int
    panel: str


class RateCallback(CallbackData, prefix="rate"):
    """half = rating × 2 (7 → 3.5); 0 clears the rating."""

    book_id: int
    half: int


class ProgressCallback(CallbackData, prefix="prog"):
    """delta > 0: add pages; 0: ask for a page number; -1: finished the book."""

    book_id: int
    delta: int
