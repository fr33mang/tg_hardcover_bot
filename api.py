import json

import httpx
from config import HARDCOVER_API_URL


class HardcoverAPI:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def execute_query(self, query: str, variables: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                HARDCOVER_API_URL,
                headers=self.headers,
                json={"query": query, "variables": variables or {}},
            )
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                raise ValueError(data["errors"][0]["message"])
            return data["data"]

    async def get_me(self) -> dict | None:
        query = "{ me { username id } }"
        data = await self.execute_query(query)
        users = data.get("me")
        return users[0] if users else None

    async def search_books(self, query: str, limit: int = 5) -> list[dict]:
        gql = """
        query Search($q: String!, $per_page: Int!) {
            search(query: $q, query_type: "Book", per_page: $per_page) {
                results
            }
        }
        """
        data = await self.execute_query(gql, {"q": query, "per_page": limit})
        raw = data.get("search", {}).get("results", {})
        if isinstance(raw, str):
            raw = json.loads(raw)
        hits = raw.get("hits", [])
        books = []
        for hit in hits:
            doc = hit.get("document", {})
            contributions = doc.get("contributions", [])
            authors = [
                c["author"]["name"]
                for c in contributions
                if c.get("author") and not c.get("contribution")
            ]
            books.append({
                "id": int(doc["id"]),
                "title": doc.get("title", ""),
                "slug": doc.get("slug", ""),
                "authors": authors,
                "release_year": doc.get("release_year"),
                "image_url": (doc.get("image") or {}).get("url"),
            })
        return books

    async def search_books_by_isbn(self, isbn: str) -> list[dict]:
        gql = """
        query SearchByISBN($isbn: String!) {
            editions(where: {isbn_13: {_eq: $isbn}}, limit: 1) {
                book { id title slug release_year
                    contributions { author { name } contribution }
                }
            }
        }
        """
        try:
            data = await self.execute_query(gql, {"isbn": isbn})
            editions = data.get("editions", [])
            books = []
            for ed in editions:
                b = ed.get("book")
                if not b:
                    continue
                authors = [
                    c["author"]["name"]
                    for c in (b.get("contributions") or [])
                    if c.get("author") and not c.get("contribution")
                ]
                books.append({
                    "id": b["id"],
                    "title": b.get("title", ""),
                    "slug": b.get("slug", ""),
                    "authors": authors,
                    "release_year": b.get("release_year"),
                })
            return books
        except Exception:
            return []

    async def get_my_shelves(self) -> dict:
        gql = """
        query {
            me {
                want_count: user_books_aggregate(where: {status_id: {_eq: 1}}) { aggregate { count } }
                reading_count: user_books_aggregate(where: {status_id: {_eq: 2}}) { aggregate { count } }
                read_count: user_books_aggregate(where: {status_id: {_eq: 3}}) { aggregate { count } }
            }
        }
        """
        data = await self.execute_query(gql)
        me = data.get("me", [{}])[0]
        return {
            "want_to_read": me.get("want_count", {}).get("aggregate", {}).get("count", 0),
            "reading": me.get("reading_count", {}).get("aggregate", {}).get("count", 0),
            "read": me.get("read_count", {}).get("aggregate", {}).get("count", 0),
        }

    async def get_shelf_books(self, status_id: int, limit: int = 10, offset: int = 0) -> list[dict]:
        gql = """
        query GetShelfBooks($status_id: Int!, $limit: Int!, $offset: Int!) {
            me {
                user_books(
                    where: {status_id: {_eq: $status_id}},
                    limit: $limit,
                    offset: $offset,
                    order_by: {updated_at: desc}
                ) {
                    id
                    rating
                    book { id title slug release_year
                        contributions { author { name } contribution }
                    }
                }
            }
        }
        """
        data = await self.execute_query(gql, {"status_id": status_id, "limit": limit, "offset": offset})
        me = data.get("me", [{}])
        return me[0].get("user_books", []) if me else []

    async def get_user_book(self, book_id: int) -> dict | None:
        gql = """
        query GetUserBook($book_id: Int!) {
            me {
                user_books(where: {book_id: {_eq: $book_id}}, limit: 1) {
                    id status_id rating
                }
            }
        }
        """
        data = await self.execute_query(gql, {"book_id": book_id})
        me = data.get("me", [{}])
        books = me[0].get("user_books", []) if me else []
        return books[0] if books else None

    async def add_book_to_shelf(self, book_id: int, status_id: int) -> dict:
        gql = """
        mutation AddBook($book_id: Int!, $status_id: Int!) {
            insert_user_book(object: {book_id: $book_id, status_id: $status_id}) {
                id
            }
        }
        """
        data = await self.execute_query(gql, {"book_id": book_id, "status_id": status_id})
        return data.get("insert_user_book", {})

    async def update_book_status(self, user_book_id: int, status_id: int) -> dict:
        gql = """
        mutation UpdateStatus($id: Int!, $status_id: Int!) {
            update_user_book_by_pk(pk_columns: {id: $id}, _set: {status_id: $status_id}) {
                id status_id
            }
        }
        """
        data = await self.execute_query(gql, {"id": user_book_id, "status_id": status_id})
        return data.get("update_user_book_by_pk", {})

    async def rate_book(self, user_book_id: int, rating: float) -> dict:
        gql = """
        mutation RateBook($id: Int!, $rating: numeric!) {
            update_user_book_by_pk(pk_columns: {id: $id}, _set: {rating: $rating}) {
                id rating
            }
        }
        """
        data = await self.execute_query(gql, {"id": user_book_id, "rating": rating})
        return data.get("update_user_book_by_pk", {})

    async def add_or_update_book(self, book_id: int, status_id: int, rating: float | None = None) -> dict:
        existing = await self.get_user_book(book_id)
        if existing:
            result = await self.update_book_status(existing["id"], status_id)
            if rating is not None:
                await self.rate_book(existing["id"], rating)
            return result
        else:
            result = await self.add_book_to_shelf(book_id, status_id)
            if rating is not None and result.get("id"):
                await self.rate_book(result["id"], rating)
            return result
