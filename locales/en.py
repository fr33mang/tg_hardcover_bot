STRINGS: dict[str, str] = {
    # bot command menu
    "cmd_search": "Search for books",
    "cmd_library": "Your reading library",
    "cmd_import": "Import from Goodreads CSV",
    "cmd_language": "Change language",
    "cmd_help": "Show available commands",
    "cmd_token": "Authorize with Hardcover token",
    "cmd_logout": "Log out",
    # auth
    "already_authorized": "You're already signed in. Type a book title to search. Buttons below: reading now, library, settings.",
    "start_welcome": (
        "👋 Hi! This is a bot for <b>Hardcover.app</b>: search, shelves and lists right from Telegram.\n\n"
        "To get started you need a Hardcover API key:\n"
        "1. Tap the button below — it opens the new-key form with the permissions the bot needs already checked.\n"
        "2. Give the key a name, pick an expiry and create it.\n"
        "3. Copy the key and <b>just send it here as a plain message</b>, no command needed.\n\n"
        "<i>The message with the key will be deleted from the chat.</i>"
    ),
    "token_prompt": (
        "Send your Hardcover API key <b>as a plain message</b> — just paste it into the chat.\n\n"
        "Don't have one? Tap the button below: it opens the form with the right permissions already checked. "
        "Name the key, pick an expiry, create and copy it.\n\n"
        "<i>The message with the key will be deleted from the chat.</i>"
    ),
    "token_empty": "The key is empty. Send it again.",
    "token_invalid": (
        "That key didn't work. Check that you copied all of it and that it hasn't expired, then send it again.\n"
        "No key yet? Create one with the button below."
    ),
    "auth_success": (
        "✅ Signed in as @{username}\n\n" "Type a book title to search. Buttons below: reading now, library, settings."
    ),
    "auth_error": "Couldn't verify the key. Try again in a moment.",
    "logged_out": "Signed out. The key was removed from the bot's database. /start to sign in again.",
    "help_authorized": (
        "📚 <b>Hardcover Bot</b>\n\n"
        "Type a book title, an author or an ISBN to search.\n\n"
        "📖 Reading — books in progress\n"
        "📚 Library — shelves and lists\n"
        "⚙️ More — language, Goodreads import, key, sign out\n\n"
        "Commands: /library, /import, /language, /token, /logout"
    ),
    # reply keyboard + settings screen
    "btn_menu_reading": "📖 Reading",
    "btn_menu_library": "📚 Library",
    "btn_menu_search": "🔍 Search",
    "btn_menu_more": "⚙️ More",
    "btn_create_key": "🔑 Create a key on Hardcover",
    "reading_empty": "📖 You're not reading anything right now.\n\nType a book title — I'll find it and offer to add it.",
    "search_prompt": "🔍 Type a book title, an author or an ISBN.",
    "more_title": "⚙️ <b>Settings</b>",
    "btn_more_language": "🌐 Language",
    "btn_more_import": "📥 Import from Goodreads",
    "btn_more_token": "🔑 Update Hardcover key",
    "btn_more_logout": "🚪 Sign out",
    # search
    "search_usage": "Usage: /search &lt;book title&gt;",
    "auth_required": "Please authorize first: /token",
    "search_error": "Search error: {e}",
    "no_books_found": "No books found.",
    "btn_prev": "← Back",
    "btn_next": "More →",
    "btn_back": "← Back",
    "btn_close": "✕ Close",
    "search_expired": "Search results expired — type the title again.",
    "no_more_results": "No more results.",
    "btn_delete_status": "🗑 Remove status",
    "btn_add_to_list": "📋 Add to list",
    "btn_open_hardcover": "🔗 Open on Hardcover",
    "status_added": "{label} — added!",
    "book_deleted": "Book removed.",
    "no_lists": "You have no lists on Hardcover.",
    "removed_from_list": "Removed from list.",
    "added_to_list": "Added to list!",
    "inline_auth_prompt": "Authorize in the bot",
    "search_hint": "Tap a number to see book details",
    "error_generic": "Error: {e}",
    "book_not_found": "Book not found.",
    "load_error": "Error loading book: {e}",
    "ratings_count": "{count} ratings",
    "et_al": "et al.",
    # shelves
    "library_title": "📖 <b>Library</b>",
    "list_empty": "List is empty.",
    "page_indicator": "(page {page})",
    "shelf_hint": "Tap a number to manage the book",
    "btn_library": "📖 Library",
    "btn_back_nav": "← Back",
    "btn_forward_nav": "Forward →",
    # import
    "import_prompt": (
        "Send the file <b>goodreads_library_export.csv</b>\n\n"
        "Export it at goodreads.com: My Books → Import/Export → Export Library\n\n"
        "Send /cancel to abort"
    ),
    "import_wrong_file": "Please send a .csv file or /cancel to abort.",
    "import_downloading": "⏳ Downloading file...",
    "import_found": "📋 Found {total} books. Starting import...",
    "import_progress": "⏳ Processing {i}/{total}...\n✅ {ok} added | ⏭ {skipped} skipped | ❌ {failed} errors",
    "import_done": "✅ Import complete!\n\nAdded: {ok}\nSkipped: {skipped}\nNot found: {failed}",
    "import_not_found_header": "\n\nNot found:\n",
    "import_more": "...and {n} more",
    "cancelled": "Cancelled.",
    "nothing_to_cancel": "No active operation to cancel.",
    # language
    "language_choose": "Choose language:",
    "language_set": "Language changed: {name}",
    # status labels (full, with emoji)
    "status_1": "📚 Want to read",
    "status_2": "📖 Reading",
    "status_3": "✅ Read",
    "status_4": "⏸ On hold",
    "status_5": "❌ Did not finish",
    "status_6": "🙈 Ignored",
    # status labels (short, with emoji)
    "status_1_short": "📚 Want",
    "status_2_short": "📖 Reading",
    "status_3_short": "✅ Read",
    "status_4_short": "⏸ On hold",
    "status_5_short": "❌ DNF",
    "status_6_short": "🙈 Ignore",
}
