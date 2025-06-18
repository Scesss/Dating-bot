import database.sqlite3 as sqlite3
import requests
import math
import os

SERVER_IP = os.getenv("SERVER_IP")
SERVER_URL = f"http://{SERVER_IP}:5000/query"

# Инициализация соединения с БД (файл 'database.db')
conn = sqlite3.connect('profiles.db')
cursor = conn.cursor()



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
    current_city: str = None,
    current_lat: float = None,
    current_lon: float = None,
) -> dict | None:
    """Найти следующую анкету:
       – пол кандидата = ваше предпочтение
       – предпочтение кандидата = ваш пол
       – не показывать уже лайкнутых
       – сначала анкеты из вашего города
       – если есть координаты, считаем расстояние и сортируем по нему
    """
    
    # 1) Собираем список лайкнутых, чтобы их исключить
    cursor.execute(
    "SELECT liked_user_id FROM likes WHERE user_id=?",
    (current_user_id,)
)
    liked_rows = cursor.fetchall()
    # Если курсор возвращает dict-подобные строки:
    liked = { row['liked_user_id'] for row in liked_rows }
    # Если вдруг остаются кортежи, можно на всякий случай так:
    # liked = { row[0] if isinstance(row, (list, tuple)) else row['liked_user_id'] for row in liked_rows }

    # 2) Выбираем всех подходящих по полу и предпочтению
    cursor.execute(
        """
        SELECT user_id,name,age,gender,looking_for,bio,photo_id,city,lat,lon
          FROM profiles
         WHERE user_id != ?
           AND gender = ?
           AND looking_for = ?
        """,
        (current_user_id, current_preference, current_gender)
    )
    cols = [d[0] for d in cursor.description]
    candidates = [
        dict(zip(cols, row))
        for row in cursor.fetchall()
        if row[0] not in liked
    ]

    if not candidates:
        return None

    # 3) Разбиваем на тех, кто из вашего города, и остальных
    same_city = []
    others    = []
    for p in candidates:
        if current_city and p.get('city') == current_city:
            same_city.append(p)
        else:
            others.append(p)

    # 4) Хаверсин для расстояния
    def haversine(lat1, lon1, lat2, lon2):
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlon/2)**2
        return 2 * 6371 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # 5) Подсчитываем distance_km, если есть обе пары координат
    for p in same_city + others:
        lat2, lon2 = p.get('lat'), p.get('lon')
        if (
            current_lat is not None and current_lon is not None
            and lat2 is not None and lon2 is not None
        ):
            p['distance_km'] = round(
                haversine(current_lat, current_lon, lat2, lon2), 2
            )
        else:
            p['distance_km'] = None

    # 6) Сортируем: сначала по городу (distance уже мелкий), внутри — по расстоянию
    same_city.sort(key=lambda x: x['distance_km'] or float('inf'))
    others.sort(   key=lambda x: x['distance_km'] or float('inf'))

    # 7) Объединяем и возвращаем первую анкету
    next_profile = (same_city + others)[0]
    return next_profile
