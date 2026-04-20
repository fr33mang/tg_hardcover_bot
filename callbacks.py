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
