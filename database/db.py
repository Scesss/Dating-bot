import aiosqlite
from config import DB_PATH

CREATE_PROFILES = """
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    gender TEXT,
    about TEXT,
    age INTEGER,
    city TEXT,
    preference TEXT
);
"""
CREATE_LIKES = """
CREATE TABLE IF NOT EXISTS likes (
    liker INTEGER,
    liked INTEGER,
    UNIQUE(liker, liked)
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_PROFILES)
        await db.execute(CREATE_LIKES)
        await db.commit()

async def get_profile(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT username,name,gender,about,age,city,preference FROM profiles WHERE user_id=?", (user_id,))
        row = await cursor.fetchone()
        if row:
            keys = ["username","name","gender","about","age","city","preference"]
            return dict(zip(keys, row))
        return None

async def save_profile(user_id, username, name, gender, about, age, city, preference):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO profiles (user_id,username,name,gender,about,age,city,preference) VALUES (?,?,?,?,?,?,?,?)",
            (user_id, username, name, gender, about, age, city, preference)
        )
        await db.commit()

async def update_field(user_id, field, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE profiles SET {field}=? WHERE user_id=?", (value, user_id))
        await db.commit()

async def get_other_profiles(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id,username,name,gender,about,age,city,preference FROM profiles WHERE user_id!=?", (user_id,))
        rows = await cursor.fetchall()
        keys = ["user_id","username","name","gender","about","age","city","preference"]
        return [dict(zip(keys, r)) for r in rows]

async def save_like(liker, liked):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO likes (liker,liked) VALUES (?,?)", (liker, liked))
        await db.commit()

async def get_likes_of_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT liked FROM likes WHERE liker=?", (user_id,))
        return [r[0] for r in await cursor.fetchall()]

async def get_liked_by(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT liker FROM likes WHERE liked=?", (user_id,))
        return [r[0] for r in await cursor.fetchall()]
