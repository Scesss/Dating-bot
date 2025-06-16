import sqlite3

# Инициализация соединения с БД (файл 'database.db')
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    # Создание таблиц, если не существуют
    cursor.execute("""CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        looking_for TEXT,
        bio TEXT,
        photo_id TEXT,
        city TEXT,
        lat REAL,
        lon REAL
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS likes (
        user_id INTEGER,
        liked_user_id INTEGER,
        UNIQUE(user_id, liked_user_id)
    )""")
    conn.commit()

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
    row = cursor.fetchone()
    if row:
        # Преобразуем результат в словарь для удобства
        cols = [desc[0] for desc in cursor.description]
        profile = dict(zip(cols, row))
        return profile
    return None

def update_profile_field(user_id, field, value):
    """Обновить одно поле анкеты."""
    allowed_fields = {"name", "age", "gender", "looking_for", "bio", "photo_id", "city", "lat", "lon"}
    if field not in allowed_fields:
        return False
    cursor.execute(f"UPDATE profiles SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    return cursor.rowcount > 0

def add_like(user_id, liked_user_id):
    """Сохранить лайк пользователя user_id к анкете liked_user_id."""
    cursor.execute("INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)", (user_id, liked_user_id))
    conn.commit()

def user_liked(user_id, target_id):
    """Проверить, лайкнул ли user_id анкету target_id."""
    cursor.execute("SELECT 1 FROM likes WHERE user_id = ? AND liked_user_id = ?", (user_id, target_id))
    return cursor.fetchone() is not None

def get_next_profile(current_user_id, current_gender, current_preference):
    """Найти подходящую анкету для текущего пользователя по критериям."""
    cursor.execute(
        """SELECT user_id, name, age, gender, looking_for, bio, photo_id, city 
           FROM profiles 
           WHERE user_id != ? 
             AND gender = ? 
             AND looking_for = ? 
             AND user_id NOT IN (
                   SELECT liked_user_id FROM likes WHERE user_id = ?
               )
           ORDER BY RANDOM() 
           LIMIT 1""",
        (current_user_id,
         # текущий пользователь ищет current_preference, значит пол анкеты = current_preference
         # и предпочтения анкеты = пол текущего пользователя
         current_preference,
         current_gender,
         current_user_id)
    )
    result = cursor.fetchone()
    if result:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, result))
    return None
