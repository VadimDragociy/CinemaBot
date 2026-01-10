from datetime import datetime, timezone
import aiosqlite

from collections import Counter
import os

DB_PATH = os.path.dirname(os.path.abspath(__file__)) + "/db_users/movies_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                title TEXT,
                url TEXT,
                ts TEXT NOT NULL
            );
        """)
        await db.commit()


async def save_history(user_id: int, query: str, title: str | None, url: str | None = ""):
    ts = datetime.now(timezone.utc).astimezone()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history(user_id, query, title, url, ts) VALUES (?, ?, ?, ?, ?)",
            (user_id, query, title, url, ts)
        )
        await db.commit()


async def get_history(user_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT query, title, url, ts FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = await cur.fetchall()
        return rows

async def get_stats(user_id: int, limit: int = 10):
    """
    Возвращает агрегированную статистику запросов пользователя.
    limit — количество последних записей истории, участвующих в статистике.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT query
            FROM history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        rows = await cur.fetchall()

    if not rows:
        return []

    counter = Counter(row[0] for row in rows)

    return counter.most_common()
