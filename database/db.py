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

# def get_next_profile(
#     current_user_id: int,
#     current_gender: str,
#     current_preference: str,
#     current_city: str = None,
#     current_lat: float = None,
#     current_lon: float = None,
# ) -> dict | None:
#     """Найти следующую анкету:
#        – пол кандидата = ваше предпочтение
#        – предпочтение кандидата = ваш пол
#        – не показывать уже лайкнутых
#        – сначала анкеты из вашего города
#        – если есть координаты, считаем расстояние и сортируем по нему
#     """
#
#     # 1) Собираем список лайкнутых, чтобы их исключить
#     cursor.execute(
#     "SELECT liked_user_id FROM likes WHERE user_id=?",
#     (current_user_id,)
# )
#     # liked_rows = cursor.fetchall()
#     # Если курсор возвращает dict-подобные строки:
#     # liked = { row['liked_user_id'] for row in liked_rows }
#     # Если вдруг остаются кортежи, можно на всякий случай так:
#     # liked = { row[0] if isinstance(row, (list, tuple)) else row['liked_user_id'] for row in liked_rows }
#
#     # logger.info("LIKED rows raw: %r", liked_rows)
#     # logger.info("LIKED set   : %r", liked)
#
#     #
#     # cursor.execute("""SELECT COUNT(*) FROM profiles
#     #     WHERE user_id != 1234
#     #     AND gender = 'Девушка'
#     #     AND looking_for = 'Парни'""")
#     # logging.info(cursor.fetchone())
#     # 2) Выбираем всех подходящих по полу и предпочтению
#     cursor.execute(
#         """
#         SELECT user_id,name,age,gender,looking_for,bio,photo_id,city,lat,lon
#           FROM profiles
#          WHERE user_id != ?
#            AND gender = ?
#            AND looking_for = ?
#         """,
#         (current_user_id, current_preference, current_gender)
#     )
#     cols = [d[0] for d in cursor.description]
#     candidates = [
#         dict(zip(cols, row))
#         for row in cursor.fetchall()
#         # if row[0] not in liked
#     ]
#
#     if not candidates:
#         return None
#
#     # 3) Разбиваем на тех, кто из вашего города, и остальных
#     same_city = []
#     others    = []
#     for p in candidates:
#         if current_city and p.get('city') == current_city:
#             same_city.append(p)
#         else:
#             others.append(p)
#
#     # 4) Хаверсин для расстояния
#     def haversine(lat1, lon1, lat2, lon2):
#         phi1, phi2 = math.radians(lat1), math.radians(lat2)
#         dphi = math.radians(lat2 - lat1)
#         dlon = math.radians(lon2 - lon1)
#         a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlon/2)**2
#         return 2 * 6371 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#
#     # 5) Подсчитываем distance_km, если есть обе пары координат
#     for p in same_city + others:
#         lat2, lon2 = p.get('lat'), p.get('lon')
#         if (
#             current_lat is not None and current_lon is not None
#             and lat2 is not None and lon2 is not None
#         ):
#             p['distance_km'] = round(
#                 haversine(current_lat, current_lon, lat2, lon2), 2
#             )
#         else:
#             p['distance_km'] = None
#
#     # 6) Сортируем: сначала по городу (distance уже мелкий), внутри — по расстоянию
#     same_city.sort(key=lambda x: x['distance_km'] or float('inf'))
#     others.sort(   key=lambda x: x['distance_km'] or float('inf'))
#
#     # 7) Объединяем и возвращаем первую анкету
#     next_profile = (same_city + others)[0]
#     return next_profile


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
    WHERE 
        p.user_id != :current_user_id
        AND p.gender = :wanted_gender
        AND p.looking_for = :wanted_looking_for
    ORDER BY RANDOM()
    LIMIT 1
    """

    params = {
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