import os

import aiosqlite
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.environ.get("REMINDER_DB_PATH", "data/reminders.db")


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                channel_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                interval TEXT,
                expires_at TEXT,
                tts INTEGER DEFAULT 0,
                timezone TEXT DEFAULT 'Asia/Tokyo',
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def add_reminder(
    user_id: int,
    channel_id: int,
    content: str,
    remind_at: datetime,
    guild_id: Optional[int] = None,
    interval: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    tts: bool = False,
    timezone_str: str = "Asia/Tokyo",
) -> int:
    now = datetime.now(timezone.utc)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO reminders
            (user_id, guild_id, channel_id, content, remind_at, interval, expires_at, tts, timezone, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                guild_id,
                channel_id,
                content,
                remind_at.isoformat(),
                interval,
                expires_at.isoformat() if expires_at else None,
                int(tts),
                timezone_str,
                1,
                now.isoformat(),
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_enabled_reminders():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE enabled = 1 ORDER BY remind_at ASC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_reminders_by_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE user_id = ? AND enabled = 1 ORDER BY remind_at ASC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_reminder_by_id(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def disable_reminder(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reminders SET enabled = 0 WHERE id = ?", (reminder_id,)
        )
        await db.commit()


async def delete_reminder(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()


async def delete_reminders_by_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM reminders WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def update_reminder_time(reminder_id: int, remind_at: datetime):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE reminders SET remind_at = ? WHERE id = ?",
            (remind_at.isoformat(), reminder_id),
        )
        await db.commit()
