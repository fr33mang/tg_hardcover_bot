STRINGS: dict[str, str] = {
    # auth
    "already_authorized": "You're already authorized. Use /shelves, /search, or /import.",
    "start_welcome": (
        "👋 Hi! This is a bot for Hardcover.\n\n"
        "To get started:\n"
        "1. Log in at <a href='https://hardcover.app'>hardcover.app</a>\n"
        "2. Go to Settings → Account → API Token\n"
        "3. Copy the token and send /token\n\n"
        "Available commands after authorization:\n"
        "/shelves — your reading statuses\n"
        "/search — search for books\n"
        "/import — import from Goodreads CSV"
    ),
    "token_prompt": (
        "Send your Bearer token from Hardcover.\n"
        "You can find it at Settings → Account → API Token on hardcover.app\n\n"
        "<i>The message with the token will be deleted for security.</i>"
    ),
    "token_empty": "Token cannot be empty. Try /token again.",
    "token_invalid": "Token is invalid. Check it and try /token again.",
    "auth_success": (
        "✅ Authorized as @{username}\n\n"
        "Now available:\n"
        "/shelves — your reading statuses\n"
        "/search — search for books\n"
        "/import — import from Goodreads CSV"
    ),
    "auth_error": "Authorization error: {e}\nTry /token again.",
    "logged_out": "You've been logged out. Use /token to authorize again.",
    # search
    "search_usage": "Usage: /search &lt;book title&gt;",
    "auth_required": "Please authorize first: /token",
    "search_error": "Search error: {e}",
    "no_books_found": "No books found.",
    "btn_prev": "← Back",
    "btn_next": "More →",
    "btn_close": "✕ Close",
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
