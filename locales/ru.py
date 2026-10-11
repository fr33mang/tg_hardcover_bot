STRINGS: dict[str, str] = {
    # bot command menu
    "cmd_search": "Поиск книг",
    "cmd_library": "Книжная библиотека",
    "cmd_import": "Импорт из Goodreads CSV",
    "cmd_language": "Сменить язык",
    "cmd_help": "Список команд",
    "cmd_token": "Авторизация через токен Hardcover",
    "cmd_logout": "Выйти",
    # auth
    "already_authorized": "Ты уже авторизован. Напиши название книги — найду. Кнопки снизу: что читаю, библиотека, настройки.",
    "start_welcome": (
        "👋 Привет! Это бот для <b>Hardcover.app</b>: поиск книг, полки, списки — прямо из Telegram.\n\n"
        "Чтобы начать, нужен API-ключ Hardcover:\n"
        "1. Нажми кнопку ниже — откроется форма нового ключа с уже отмеченными правами, которые нужны боту.\n"
        "2. Дай ключу имя, выбери срок действия и создай его.\n"
        "   Если открывал страницу сам, отметь права:\n<code>{scopes}</code>\n"
        "3. Скопируй ключ и <b>просто пришли его сюда одним сообщением</b>, без команд.\n\n"
        "<i>Сообщение с ключом будет удалено из чата.</i>"
    ),
    "token_prompt": (
        "Пришли API-ключ Hardcover <b>одним сообщением</b> — просто вставь его в чат.\n\n"
        "Нет ключа? Нажми кнопку ниже: откроется форма с уже отмеченными правами. "
        "Дай ключу имя, выбери срок действия, создай и скопируй.\n"
        "Если открывал страницу сам, отметь права:\n<code>{scopes}</code>\n\n"
        "<i>Сообщение с ключом будет удалено из чата.</i>"
    ),
    "token_empty": "Ключ пустой. Пришли его ещё раз.",
    "token_invalid": (
        "Ключ не подошёл. Проверь, что скопировал его целиком и что срок действия не истёк, и пришли ещё раз.\n"
        "Если ключа нет — создай по кнопке ниже."
    ),
    "auth_success": (
        "✅ Авторизован как @{username}\n\n"
        "Просто напиши название книги — найду. Кнопки снизу: что читаю, библиотека, настройки."
    ),
    "auth_error": "Не удалось проверить ключ. Попробуй ещё раз чуть позже.",
    "logged_out": "Вышел. Ключ удалён из базы бота. /start — чтобы войти снова.",
    "help_authorized": (
        "📚 <b>Hardcover Bot</b>\n\n"
        "Напиши название книги, автора или ISBN — найду.\n\n"
        "📖 Читаю — книги в процессе\n"
        "📚 Библиотека — полки и списки\n"
        "⚙️ Ещё — язык, импорт из Goodreads, ключ, выход\n\n"
        "Команды: /library, /import, /language, /token, /logout"
    ),
    # reply keyboard + settings screen
    "btn_menu_reading": "📖 Читаю",
    "btn_menu_library": "📚 Библиотека",
    "btn_menu_search": "🔍 Поиск",
    "btn_menu_more": "⚙️ Ещё",
    "btn_create_key": "🔑 Создать ключ на Hardcover",
    "reading_empty": "📖 Сейчас ничего не читаешь.\n\nНапиши название книги — найду и предложу добавить.",
    "search_prompt": "🔍 Напиши название книги, автора или ISBN.",
    "more_title": "⚙️ <b>Настройки</b>",
    "btn_more_language": "🌐 Язык",
    "btn_more_import": "📥 Импорт из Goodreads",
    "btn_more_token": "🔑 Обновить ключ Hardcover",
    "btn_more_logout": "🚪 Выйти",
    # search
    "search_usage": "Использование: /search &lt;название книги&gt;",
    "auth_required": "Сначала авторизуйтесь: /token",
    "search_error": "Ошибка поиска: {e}",
    "no_books_found": "Книги не найдены.",
    "btn_prev": "← Назад",
    "btn_next": "Ещё →",
    "btn_back": "← Назад",
    "btn_close": "✕ Закрыть",
    "search_expired": "Результаты поиска устарели — напишите название ещё раз.",
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
    "language_set": "Язык изменён: {name}",
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
