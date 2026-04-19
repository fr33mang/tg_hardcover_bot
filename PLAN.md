# Plan: Hardcover Telegram Bot

## Context

Goodreads закрыли публичное API, старый бот (python-telegram-bot 13.0 + OAuth1) умер.
Цель — новый бот для Hardcover: GraphQL API, Bearer-токен вместо OAuth, более современный стек.
Пользователь хочет не копию старого бота, а продуманное решение с использованием современных возможностей Telegram.

---

## Ключевые отличия от старого подхода

| Аспект | Старый бот | Новый бот |
|---|---|---|
| Auth | Goodreads OAuth1 (редирект → callback → токены) | Простой Bearer токен — пользователь вставляет `/token <токен>` |
| Telegram lib | python-telegram-bot 13.0 (sync) | **aiogram 3.x** (async, роутеры, FSM) |
| HTTP | rauth + requests (sync) | **httpx** (async) |
| API | REST + XML парсинг | **GraphQL** (чистые JSON-запросы) |
| Инлайн | Базовый | Полноценный inline mode для поиска в любом чате |

---

## Стек

- **Python 3.12**
- **aiogram 3.x** — async, роутеры, FSM для многошаговых сценариев (отзыв, импорт)
- **httpx** — async GraphQL запросы к `https://api.hardcover.app/v1/graphql`
- **SQLite** (через aiosqlite) — хранит `telegram_id → bearer_token`. Проще деплоя, нет отдельного контейнера, достаточно для нагрузки одного бота. Токены Hardcover — низкорисковые (книжная полка, не платёжные данные). Если в будущем нужны несколько инстансов — мигрировать на Postgres.
- **Docker + docker-compose** (один контейнер, SQLite файл в volume)

---

## Структура проекта

```
handcover_bot/
├── bot.py              # точка входа, aiogram App
├── config.py           # env vars
├── db.py               # aiosqlite, таблица users(id, token)
├── api.py              # HardcoverAPI — async GraphQL клиент
├── handlers/
│   ├── auth.py         # /start, /token, /logout
│   ├── search.py       # поиск + inline query
│   ├── shelves.py      # /shelves, browse books
│   ├── book.py         # детали книги + добавить на полку + рейтинг
│   └── import_csv.py   # /import — парсинг Goodreads CSV
├── queries/            # GraphQL строки (отдельные файлы .graphql или константы)
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

---

## Hardcover API — ключевые операции

**Статусы книг:** `1` = хочу прочитать, `2` = читаю, `3` = прочитал

```graphql
# Поиск
query { books(where: {title: {_ilike: "%query%"}}, limit: 5, order_by: {users_read_count: desc}) { id title slug cached_contributors } }

# Мои полки
query { me { user_books(where: {status_id: {_eq: 3}}) { rating book { id title } } } }

# Добавить книгу / сменить статус
mutation { insert_user_book(object: {book_id: 123, status_id: 1}) { id } }

# Рейтинг и отзыв — через update_user_book
mutation { update_user_book_by_pk(pk_columns: {id: X}, _set: {rating: 4.5, review_raw: "текст"}) { id } }
```

**Rate limit:** 60 req/min, timeout 30s. Токен живёт 1 год, сбрасывается 1 января.

---

## UX — команды и сценарии

```
/start    — приветствие, инструкция получить токен
/token    — вставить Bearer токен (FSM: ждём следующее сообщение)
/logout   — удалить токен

/shelves  — список полок с количеством книг (inline кнопки)
           → [хочу прочитать (42)] [читаю (3)] [прочитал (120)]
           → листание книг с пагинацией

/search <запрос>  — поиск книги (или просто текстовое сообщение)
   → карточки: название, автор, кнопки [+ хочу прочитать] [+ читаю] [+ прочитал]
   → /book_<slug> для деталей

/import   — FSM: ожидаем документ .csv
   → парсим Goodreads CSV
   → для каждой книги ищем в Hardcover по ISBN/названию
   → добавляем с правильным статусом + рейтингом
   → прогресс-сообщение (редактируем одно сообщение)

Inline mode: @botname dune → результаты поиска в любом чате
```

**Современные фишки aiogram 3:**
- **FSM** для `/token` (чтобы не светить токен в тексте команды) и `/import`
- **Router** по модулям вместо монолитного dispatcher
- **Inline keyboard** с callback_data через `CallbackData` factory (типобезопасно)
- Редактирование сообщений при пагинации (как в старом боте, но чище)

---

## База данных

```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    bearer_token TEXT NOT NULL,
    hardcover_username TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

Никаких OAuth-токенов, просто один Bearer токен на пользователя. SQLite + aiosqlite, файл монтируется как Docker volume (`/data/bot.db`).

---

## Файлы для создания

1. `config.py` — `TELEGRAM_BOT_TOKEN`, `DATABASE_PATH`
2. `db.py` — aiosqlite, CRUD для users
3. `api.py` — `HardcoverAPI` класс, `execute_query()`, все методы async
4. `handlers/auth.py` — start, token (FSM), logout
5. `handlers/search.py` — search + inline query
6. `handlers/shelves.py` — shelves, books pagination
7. `handlers/book.py` — book detail, add to shelf, rate
8. `handlers/import_csv.py` — import Goodreads CSV (ПЕРВЫЙ ПРИОРИТЕТ)
9. `bot.py` — aiogram App, роутеры, запуск
10. `docker-compose.yaml`, `Dockerfile`, `requirements.txt`

---

## Приоритет реализации

1. **Auth** (token / logout) — без этого ничего не работает
2. **Search + add to shelf** — основной use case
3. **/import CSV** — критично, 50+ книг не перенеслись
4. **Shelves browser** — листать свои полки
5. **Book detail + rating/review**
6. **Inline mode** — бонус

---

## Верификация

1. `docker-compose up` — бот стартует
2. `/token <valid_token>` → "Авторизован как @username"
3. Текстовый запрос "Dune" → 5 результатов с кнопками
4. Нажать "+ хочу прочитать" → книга появляется в `/shelves`
5. Загрузить тестовый Goodreads CSV → `/import` добавляет книги и репортит прогресс
6. Inline режим: `@botname Foundation` → результаты в инлайне
