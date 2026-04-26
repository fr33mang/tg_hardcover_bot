STRINGS: dict[str, str] = {
    # auth
    "already_authorized": "Вы уже авторизованы. Используйте /shelves, /search или /import.",
    "start_welcome": (
        "👋 Привет! Это бот для Hardcover.\n\n"
        "Чтобы начать:\n"
        "1. Войдите на <a href='https://hardcover.app'>hardcover.app</a>\n"
        "2. Перейдите в Settings → Account → API Token\n"
        "3. Скопируйте токен и отправьте /token\n\n"
        "После авторизации доступны команды:\n"
        "/shelves — ваши статусы\n"
        "/search — поиск книг\n"
        "/import — импорт из Goodreads CSV"
    ),
    "token_prompt": (
        "Отправьте ваш Bearer токен с Hardcover.\n"
        "Найти его можно в Settings → Account → API Token на hardcover.app\n\n"
        "<i>Сообщение с токеном будет удалено для безопасности.</i>"
    ),
    "token_empty": "Токен не может быть пустым. Попробуйте /token ещё раз.",
    "token_invalid": "Токен недействителен. Проверьте и попробуйте /token снова.",
    "auth_success": (
        "✅ Авторизован как @{username}\n\n"
        "Теперь доступны:\n"
        "/shelves — ваши статусы\n"
        "/search — поиск книг\n"
        "/import — импорт из Goodreads CSV"
    ),
    "auth_error": "Ошибка авторизации: {e}\nПопробуйте /token снова.",
    "logged_out": "Вы вышли из аккаунта. Используйте /token для повторной авторизации.",
    # search
    "search_usage": "Использование: /search &lt;название книги&gt;",
    "auth_required": "Сначала авторизуйтесь: /token",
    "search_error": "Ошибка поиска: {e}",
    "no_books_found": "Книги не найдены.",
    "btn_prev": "← Назад",
    "btn_next": "Ещё →",
    "btn_close": "✕ Закрыть",
    "no_more_results": "Больше результатов нет.",
    "btn_delete_status": "🗑 Удалить из статуса",
    "btn_add_to_list": "📋 В список",
    "btn_open_hardcover": "🔗 Открыть на Hardcover",
    "status_added": "{label} — добавлено!",
    "book_deleted": "Книга удалена.",
    "no_lists": "У вас нет списков на Hardcover.",
    "removed_from_list": "Удалено из списка.",
    "added_to_list": "Добавлено в список!",
    "inline_auth_prompt": "Авторизуйтесь в боте",
    "search_hint": "Нажмите на номер книги для подробностей",
    "error_generic": "Ошибка: {e}",
    "book_not_found": "Книга не найдена.",
    "load_error": "Ошибка загрузки книги: {e}",
    "ratings_count": "{count} оценок",
    "et_al": "и др.",
    # shelves
    "library_title": "📖 <b>Библиотека</b>",
    "list_empty": "Список пуст.",
    "page_indicator": "(стр. {page})",
    "shelf_hint": "Нажмите на номер для управления книгой",
    "btn_library": "📖 Библиотека",
    "btn_back_nav": "← Назад",
    "btn_forward_nav": "Вперёд →",
    # import
    "import_prompt": (
        "Отправьте файл <b>goodreads_library_export.csv</b>\n\n"
        "Экспортировать можно на goodreads.com: My Books → Import/Export → Export Library\n\n"
        "Для отмены отправьте /cancel"
    ),
    "import_wrong_file": "Пожалуйста, отправьте файл .csv или /cancel для отмены.",
    "import_downloading": "⏳ Загружаю файл...",
    "import_found": "📋 Найдено {total} книг. Начинаю импорт...",
    "import_progress": "⏳ Обрабатываю {i}/{total}...\n✅ {ok} добавлено | ⏭ {skipped} пропущено | ❌ {failed} ошибок",
    "import_done": "✅ Импорт завершён!\n\nДобавлено: {ok}\nПропущено: {skipped}\nНе найдено: {failed}",
    "import_not_found_header": "\n\nНе найдены:\n",
    "import_more": "...и ещё {n}",
    "cancelled": "Отменено.",
    "nothing_to_cancel": "Нет активной операции для отмены.",
    # language
    "language_choose": "Выберите язык:",
    "language_set": "Язык изменён: {lang}",
    # status labels (full, with emoji)
    "status_1": "📚 Хочу прочитать",
    "status_2": "📖 Читаю",
    "status_3": "✅ Прочитал",
    "status_4": "⏸ Пауза",
    "status_5": "❌ Не закончил",
    "status_6": "🙈 Игнор",
    # status labels (short, with emoji)
    "status_1_short": "📚 Хочу",
    "status_2_short": "📖 Читаю",
    "status_3_short": "✅ Прочитал",
    "status_4_short": "⏸ Пауза",
    "status_5_short": "❌ Не закончил",
    "status_6_short": "🙈 Игнор",
}
