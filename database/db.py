import logging

import database.sqlite3 as sqlite3
import requests
import math
import os

SERVER_IP = os.getenv("SERVER_IP")
SERVER_URL = f"http://{SERVER_IP}:5000/query"

# Инициализация соединения с БД (файл 'database.db')
conn = sqlite3.connect('profiles.db')
cursor = conn.cursor()

logger = logging.getLogger(__name__)

def run_query(sql, params=None):
    payload = {"sql": sql, "params": params or []}
    resp = requests.post(SERVER_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

# def init_db():
#     # Создание таблиц, если не существуют
#     cursor.execute("""CREATE TABLE IF NOT EXISTS profiles (
#         user_id INTEGER PRIMARY KEY,
#         name TEXT,
#         age INTEGER,
#         gender TEXT,
#         looking_for TEXT,
#         bio TEXT,
#         photo_id TEXT,
#         city TEXT,
#         lat REAL,
#         lon REAL
#     )""")
#     cursor.execute("""CREATE TABLE IF NOT EXISTS likes (
#         user_id INTEGER,
#         liked_user_id INTEGER,
#         UNIQUE(user_id, liked_user_id)
#     )""")
#     conn.commit()

def save_profile(user_id, name, age, gender, looking_for, bio, photo_id, city=None, lat=None, lon=None):
    """Сохранить анкету пользователя (новую или обновить существующую)."""
    cursor.execute(
        """INSERT OR REPLACE INTO profiles 
           (user_id, name, age, gender, looking_for, bio, photo_id, city, lat, lon) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, age, gender, looking_for, bio, photo_id, city, lat, lon)
    )
    conn.commit()



def get_profile(user_id):
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    # теперь fetchone() даёт dict (как и прокси)
    row = cursor.fetchone()
    if row:
        # если прокси вернул dict, просто вернём его
        if isinstance(row, dict):
            return row
        # иначе — старый вариант для tuple
        cols    = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    return None

def update_profile_field(user_id, field, value):
    """Обновить одно поле анкеты."""
    allowed_fields = {"name", "age", "gender", "looking_for", "bio", "photo_id", "city", "lat", "lon"}
    if field not in allowed_fields:
        return False
    cursor.execute(f"UPDATE profiles SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    return True

def add_like(user_id, liked_user_id):
    """Сохранить лайк пользователя user_id к анкете liked_user_id."""
    cursor.execute("INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)", (user_id, liked_user_id))
    conn.commit()

def user_liked(user_id, target_id):
    """Проверить, лайкнул ли user_id анкету target_id."""
    cursor.execute("SELECT 1 FROM likes WHERE user_id = ? AND liked_user_id = ?", (user_id, target_id))
    return cursor.fetchone() is not None


def get_next_profile(
    current_user_id: int,
    current_gender: str,
    current_preference: str,
    current_city: str = None,  # пока не используем
    current_lat: float = None, # пока не используем
    current_lon: float = None, # пока не используем
) -> dict | None:
    singular = {
        "Девушки": "Девушка",
        "Парни": "Парень",
        "Девушка": "Девушка",  # Для защиты от разных форматов
        "Парень": "Парень"
    }

    plural = {
        "Парень": "Парни",
        "Девушка": "Девушки",
        "Парни": "Парни",  # Для защиты от разных форматов
        "Девушки": "Девушки"
    }

    # Нормализация входных данных
    current_gender = current_gender.strip().capitalize()
    current_preference = current_preference.strip().capitalize()

    # Определение параметров поиска
    wanted_gender = singular.get(current_preference)
    wanted_looking_for = plural.get(current_gender)

    if not wanted_gender or not wanted_looking_for:
        logger.error("Invalid gender/pref: %s/%s", current_gender, current_preference)
        return None

    sql = """
    SELECT 
        p.user_id,
        p.name,
        p.age,
        p.gender,
        p.looking_for,
        p.bio,
        p.photo_id,
        p.city,
        p.lat,
        p.lon
    FROM profiles AS p
        LEFT JOIN likes    AS l ON l.user_id = :me AND l.liked_user_id    = p.user_id
        LEFT JOIN dislikes AS d ON d.user_id = :me AND d.disliked_user_id = p.user_id
    WHERE 
        p.user_id != :current_user_id
        AND p.gender = :wanted_gender
        AND p.looking_for = :wanted_looking_for
    ORDER BY RANDOM()
    LIMIT 1
    """

    params = {
        "me": current_user_id,
        "current_user_id": current_user_id,
        "wanted_gender": wanted_gender,
        "wanted_looking_for": wanted_looking_for
    }

    try:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    except Exception as e:
        logger.error("Ошибка базы данных: %s", e)
        return None

    if not row:
        logger.info(
            "Анкеты не найдены: user_id=%s, gender=%s, preference=%s",
            current_user_id, current_gender, current_preference
        )
        return None

    # 1. ВЫПОЛНЯЕМ ЗАПРОС
    cursor.execute(sql, params)
    row = cursor.fetchone()
    cols = [d[0] for d in cursor.description]
    profile = dict(zip(cols, row))
    if profile['user_id'] == current_user_id:
        logger.critical(
            "В БД НАЙДЕНА СОБСТВЕННАЯ АНКЕТА! user_id=%s",
            current_user_id
        )
        return None
    logger.info("get_next_profile(simple) → %r", profile)
    if current_lat is not None and current_lon is not None and profile.get("lat") and profile.get("lon"):
        def haversine(lat1, lon1, lat2, lon2):
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlon / 2) ** 2
            return 2 * 6371 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        profile["distance_km"] = round(haversine(current_lat, current_lon,
                                                 profile["lat"], profile["lon"]), 2)
    else:
        profile["distance_km"] = None
    return profile

# Matches table
cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    user_id      INTEGER,
    match_id     INTEGER,
    UNIQUE(user_id, match_id)
)
""")
conn.commit()

def add_match(user_id: int, match_id: int):
    """Record a mutual match."""
    cursor.execute(
        "INSERT OR IGNORE INTO matches (user_id, match_id) VALUES (?, ?)",
        (user_id, match_id)
    )
    conn.commit()

def get_matches(user_id: int) -> list[int]:
    """Return list of user_ids you have mutual matches with."""
    cursor.execute(
        "SELECT match_id FROM matches WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()
    result = []
    for row in rows:
        # если row — кортеж, берём row[0]; если dict/Row — берём по имени
        try:
            result.append(row[0])
        except (KeyError, IndexError, TypeError):
            result.append(row["match_id"])
    return result

def get_liked_by(user_id: int) -> list[int]:
    """Вернуть список user_id тех, кто лайкнул данного пользователя."""
    """Кто лайкнул меня, без тех, кого я уже лайкнул/дизлайкнул или заматчил."""
    cursor.execute("""
          SELECT l.user_id
            FROM likes AS l
       LEFT JOIN dislikes AS d
         ON d.user_id = ? AND d.disliked_user_id = l.user_id
       LEFT JOIN matches AS m
         ON m.user_id = ? AND m.match_id = l.user_id
           WHERE l.liked_user_id = ?
             AND d.disliked_user_id IS NULL
             AND m.match_id        IS NULL
        """, (user_id, user_id, user_id))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        # если row — кортеж, берём row[0]; если dict/Row — берём по имени
        try:
            result.append(row[0])
        except (KeyError, IndexError, TypeError):
            result.append(row["user_id"])
    return result

cursor.execute("""
CREATE TABLE IF NOT EXISTS dislikes (
    user_id         INTEGER,
    disliked_user_id INTEGER,
    UNIQUE(user_id, disliked_user_id)
)
""")
conn.commit()

def add_dislike(user_id: int, disliked_user_id: int):
    """Записать дизлайк пользователя."""
    cursor.execute(
        "INSERT OR IGNORE INTO dislikes (user_id, disliked_user_id) VALUES (?,?)",
        (user_id, disliked_user_id)
    )
    conn.commit()