from aiogram.filters.callback_data import CallbackData


class BookDetailCallback(CallbackData, prefix="book"):
    book_id: int


class AddBookCallback(CallbackData, prefix="add"):
    book_id: int
    status_id: int


class DeleteBookCallback(CallbackData, prefix="del"):
    book_id: int
