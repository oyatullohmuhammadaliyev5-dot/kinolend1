import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                genre TEXT NOT NULL,
                file_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                total_rating REAL DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_link TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie_code TEXT,
                rating INTEGER,
                UNIQUE(user_id, movie_code)
            )
        """)
        await db.commit()


# ─── USERS ────────────────────────────────────────────────────────────────────

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def get_user_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0]


async def get_all_user_ids() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM users")
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


# ─── MOVIES ───────────────────────────────────────────────────────────────────

async def add_movie(code: str, name: str, genre: str, file_id: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO movies (code, name, genre, file_id) VALUES (?, ?, ?, ?)",
                (code, name, genre, file_id)
            )
            await db.commit()
        return True
    except Exception:
        return False


async def get_movie(code: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT code, name, genre, file_id, views, total_rating, rating_count FROM movies WHERE code=?",
            (code,)
        )
        row = await cursor.fetchone()
        if row:
            avg = round(row[5] / row[6], 1) if row[6] > 0 else 0
            return {"code": row[0], "name": row[1], "genre": row[2],
                    "file_id": row[3], "views": row[4], "avg_rating": avg,
                    "rating_count": row[6]}
        return None


async def increment_views(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET views=views+1 WHERE code=?", (code,))
        await db.commit()


async def delete_movie(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM movies WHERE code=?", (code,))
        await db.commit()
        return cursor.rowcount > 0


async def get_top_movies(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name, code, genre, views, total_rating, rating_count FROM movies ORDER BY views DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            avg = round(r[4] / r[5], 1) if r[5] > 0 else 0
            result.append({"name": r[0], "code": r[1], "genre": r[2],
                           "views": r[3], "avg_rating": avg})
        return result


async def get_movie_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM movies")
        row = await cursor.fetchone()
        return row[0]


# ─── RATINGS ──────────────────────────────────────────────────────────────────

async def add_rating(user_id: int, movie_code: str, rating: int) -> str:
    """Returns 'added', 'updated', or 'error'"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT rating FROM ratings WHERE user_id=? AND movie_code=?",
            (user_id, movie_code)
        )
        existing = await cursor.fetchone()
        if existing:
            old = existing[0]
            await db.execute(
                "UPDATE ratings SET rating=? WHERE user_id=? AND movie_code=?",
                (rating, user_id, movie_code)
            )
            await db.execute(
                "UPDATE movies SET total_rating=total_rating-?+? WHERE code=?",
                (old, rating, movie_code)
            )
            await db.commit()
            return "updated"
        else:
            await db.execute(
                "INSERT INTO ratings (user_id, movie_code, rating) VALUES (?, ?, ?)",
                (user_id, movie_code, rating)
            )
            await db.execute(
                "UPDATE movies SET total_rating=total_rating+?, rating_count=rating_count+1 WHERE code=?",
                (rating, movie_code)
            )
            await db.commit()
            return "added"


# ─── CHANNELS ─────────────────────────────────────────────────────────────────

async def get_channels() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, channel_id, channel_name, channel_link FROM channels")
        rows = await cursor.fetchall()
        return [{"id": r[0], "channel_id": r[1], "channel_name": r[2], "channel_link": r[3]}
                for r in rows]


async def add_channel(channel_id: str, channel_name: str, channel_link: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO channels (channel_id, channel_name, channel_link) VALUES (?, ?, ?)",
            (channel_id, channel_name, channel_link)
        )
        await db.commit()


async def delete_channel(channel_db_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM channels WHERE id=?", (channel_db_id,))
        await db.commit()
        return cursor.rowcount > 0
