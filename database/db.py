from .connection import get_connection
import os
from dotenv import load_dotenv

load_dotenv()

blank_photo_id = os.getenv("BLANK_PROFILE_PHOTO_ID")


class Database:
    def __init__(self):
        # Инициализация соединения и курсора
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        # Автоматически создаём таблицы при старте
        self.create_tables()

    def create_tables(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

    def create_tables(self):
        """Создает таблицы, если их еще нет."""
        self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        age INTEGER CHECK (age >= 14 AND age <= 120),
                        gender VARCHAR(20) NOT NULL,
                        looking_for VARCHAR(20) NOT NULL,
                        bio TEXT,
                        photo_id VARCHAR(100),
                        city VARCHAR(100),
                        lat DOUBLE PRECISION,
                        lon DOUBLE PRECISION,
                        balance INTEGER DEFAULT 0,
                        count_likes INTEGER DEFAULT 0,
                        count_dislikes INTEGER DEFAULT 0,
                        activated BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL REFERENCES users(user_id),
                referee_id BIGINT NOT NULL UNIQUE REFERENCES users(user_id),
                registered BOOLEAN DEFAULT FALSE,
                bonus_credited BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                liked_user_id BIGINT NOT NULL REFERENCES users(user_id),
                message TEXT,                         
                amount   INTEGER DEFAULT 0, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, liked_user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dislikes (
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                disliked_user_id BIGINT NOT NULL REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, disliked_user_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                match_id BIGINT NOT NULL REFERENCES users(user_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, match_id)
            )
        """)
        self.conn.commit()

    def create_user(self, user_data: dict):
        query = """
            INSERT INTO users (
                user_id, name, age, gender, looking_for, bio,
                photo_id, city, lat, lon
            ) VALUES (
                %(user_id)s, %(name)s, %(age)s, %(gender)s, %(looking_for)s, %(bio)s,
                %(photo_id)s, %(city)s, %(lat)s, %(lon)s
            )
            ON CONFLICT (user_id) DO UPDATE SET
                name = EXCLUDED.name,
                age = EXCLUDED.age,
                gender = EXCLUDED.gender,
                looking_for = EXCLUDED.looking_for,
                bio = EXCLUDED.bio,
                photo_id = EXCLUDED.photo_id,
                city = EXCLUDED.city,
                lat = EXCLUDED.lat,
                lon = EXCLUDED.lon,
                updated_at = CURRENT_TIMESTAMP
        """
        self.cursor.execute(query, user_data)
        self.conn.commit()

    def get_user(self, user_id: int) -> dict | None:
        self.cursor.execute(
            "SELECT * FROM users WHERE user_id = %(user_id)s",
            {"user_id": user_id}
        )
        return self.cursor.fetchone()

    def update_user(self, user_id: int, update_data: dict):
        set_clause = ", ".join([f"{key} = %({key})s" for key in update_data])
        query = f"""
            UPDATE users
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %(user_id)s
        """
        params = {**update_data, "user_id": user_id}
        self.cursor.execute(query, params)
        self.conn.commit()

    def increment_likes(self, user_id: int):
        self.cursor.execute(
            "UPDATE users SET count_likes = count_likes + 1 WHERE user_id = %s",
            (user_id,)
        )
        self.conn.commit()

    def increment_dislikes(self, user_id: int):
        self.cursor.execute(
            "UPDATE users SET count_dislikes = count_dislikes + 1 WHERE user_id = %s",
            (user_id,)
        )
        self.conn.commit()

    def activate_profile(self, user_id: int):
        self.cursor.execute(
            "UPDATE users SET activated = TRUE WHERE user_id = %s",
            (user_id,)
        )
        self.conn.commit()

    def save_profile(self, profile_data: dict):
        # Синоним для создания/обновления пользователя
        return self.create_user(profile_data)

    def get_profile(self, user_id: int) -> dict | None:
        # Синоним для получения пользователя
        return self.get_user(user_id)

    def update_profile_field(self, user_id: int, field: str, value):
        # Обновление одного поля пользователя
        return self.update_user(user_id, {field: value})

    def user_liked(self, user_id: int, liked_user_id: int) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM likes WHERE user_id = %s AND liked_user_id = %s",
            (user_id, liked_user_id)
        )
        return bool(self.cursor.fetchone())

    def get_liked_by(self, user_id: int) -> list[dict]:
        self.cursor.execute(
            """
            SELECT u.* FROM users u
            JOIN likes l ON l.user_id = u.user_id
            WHERE l.liked_user_id = %s
            """,
            (user_id,)
        )
        return self.cursor.fetchall()

    def add_like(self, user_id: int, liked_user_id: int, message: str | None = None,
             amount: int = 0) -> bool:
        self.cursor.execute(
        """
        INSERT INTO likes (user_id, liked_user_id, message, amount)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, liked_user_id) DO NOTHING
        """,
        (user_id, liked_user_id, message, amount)
        )
        self.conn.commit()
        self.increment_likes(user_id)
        self.cursor.execute(
            "SELECT 1 FROM likes WHERE user_id = %s AND liked_user_id = %s",
            (liked_user_id, user_id)
        )
        if self.cursor.fetchone():
            self.add_match(user_id, liked_user_id)
            self.add_match(liked_user_id, user_id)
            return True
        return False

    def add_match(self, user_id: int, match_id: int):
        self.cursor.execute(
            """
            INSERT INTO matches (user_id, match_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (user_id, match_id)
        )
        self.conn.commit()
    
    def add_dislike(self, user_id: int, disliked_user_id: int):
        self.cursor.execute(
            """
            INSERT INTO dislikes (user_id, disliked_user_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """,
            (user_id, disliked_user_id)
        )
        # увеличиваем счётчик дизлайков (если нужно)
        self.increment_dislikes(user_id)
        self.conn.commit()

    def user_disliked(self, user_id: int, disliked_user_id: int) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM dislikes WHERE user_id = %s AND disliked_user_id = %s",
            (user_id, disliked_user_id)
        )
        return bool(self.cursor.fetchone())

    def get_matches(self, user_id: int) -> list[dict]:
        self.cursor.execute(
            """
            SELECT u.* FROM users u
            JOIN matches m ON m.match_id = u.user_id
            WHERE m.user_id = %s
            """,
            (user_id,)
        )
        return self.cursor.fetchall()

    def get_next_profile(self, *, current_user_id: int, current_gender: str, current_preference: str,
                         current_lat: float = None, current_lon: float = None) -> dict | None:
        """
        Возвращает следующий профиль пользователя с расчетом расстояния в километрах.
        Нормализует формы и вычисляет distance_km, если координаты заданы.
        """
        # Маппинг форм
        singular = {
            "Девушки": "Девушка",
            "Парни": "Парень",
            "Девушка": "Девушка",
            "Парень": "Парень"
        }
        plural = {
            "Парень": "Парни",
            "Девушка": "Девушки",
            "Парни": "Парни",
            "Девушки": "Девушки"
        }
        # Нормализация входных данных
        current_gender = current_gender.strip().capitalize()
        current_preference = current_preference.strip().capitalize()
        wanted_gender = singular.get(current_preference)
        wanted_looking_for = plural.get(current_gender)
        if not wanted_gender or not wanted_looking_for:
            return None

        # Выборка с расчетом distance_km
        # Используем формулу Haversine для PostgreSQL
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
            p.lon,
            p.balance, 
            CASE
                WHEN %(current_lat)s IS NOT NULL AND %(current_lon)s IS NOT NULL AND p.lat IS NOT NULL AND p.lon IS NOT NULL THEN
                    6371 * acos(
                        cos(radians(%(current_lat)s)) * cos(radians(p.lat)) *
                        cos(radians(p.lon) - radians(%(current_lon)s)) +
                        sin(radians(%(current_lat)s)) * sin(radians(p.lat))
                    )
                ELSE NULL
            END AS distance_km
        FROM users AS p
        WHERE
            p.user_id != %(current_user_id)s
            AND p.gender = %(wanted_gender)s
            AND p.looking_for = %(wanted_looking_for)s
            AND p.user_id NOT IN (
                SELECT liked_user_id FROM likes WHERE user_id = %(current_user_id)s
            )
        ORDER BY distance_km NULLS LAST, RANDOM()
        LIMIT 1
        """
        params = {
            'current_user_id': current_user_id,
            'wanted_gender': wanted_gender,
            'wanted_looking_for': wanted_looking_for,
            'current_lat': current_lat,
            'current_lon': current_lon
        }
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def get_all_profiles_sorted_by_balance(self) -> list[dict]:
        """
        Возвращает список всех анкет из таблицы users,
        отсортированных по полю balance DESC.
        """
        self.cursor.execute("""
               SELECT user_id, name, age, gender, looking_for, city, bio, photo_id, balance
               FROM users
               ORDER BY balance DESC
           """)
        rows = self.cursor.fetchall()
        profiles = []
        for row in rows:
            profiles.append({
                "user_id": row["user_id"],
                "name": row["name"],
                "age": row["age"],
                "gender": row["gender"],
                "looking_for": row["looking_for"],
                "city": row["city"],
                "bio": row["bio"],
                "photo_id": row["photo_id"],
                "balance": row["balance"],
            })
        return profiles

    def change_balance(self, user_id: int, amount: int):
        """
        Плюс-минус amount к balance у user_id.
        """
        self.cursor.execute(
            """
            UPDATE users
               SET balance = balance + %s
             WHERE user_id = %s
            """,
            (amount, user_id)
        )
        self.conn.commit()

    def award_given_like(self, giver_id: int):
        self.change_balance(giver_id, 2)

    def award_given_dislike(self, giver_id: int):
        self.change_balance(giver_id, 1)

    def award_received_like(self, receiver_id: int):
        self.change_balance(receiver_id, 5)

    def award_received_dislike(self, receiver_id: int):
        self.change_balance(receiver_id, 2)

    def sleep_profile(self, user_id: int):
        """
        Затирает bio и заменяет фото на пустую-заглушку.
        """
        self.cursor.execute(
            """
            UPDATE users
               SET about = '',     -- или 'bio', как у вас колонка называется
                   photo = %s
             WHERE user_id = %s
            """,
            (blank_photo_id, user_id)
        )
        self.conn.commit()

# Модульный интерфейс для простого импорта
_db = Database()

def create_user(user_data: dict):
    return _db.create_user(user_data)

def get_user(user_id: int):
    return _db.get_user(user_id)

def update_user(user_id: int, update_data: dict):
    return _db.update_user(user_id, update_data)

def increment_likes(user_id: int):
    return _db.increment_likes(user_id)

def increment_dislikes(user_id: int):
    return _db.increment_dislikes(user_id)

def activate_profile(user_id: int):
    return _db.activate_profile(user_id)

def save_profile(**profile_data):
    """Сохраняет или обновляет профиль пользователя"""
    return _db.save_profile(profile_data)

def get_profile(*args, **kwargs) -> dict | None:
    """Принимает user_id или объект с ключом 'user_id' (RealDictRow или dict) и возвращает профиль."""
    # Извлекаем идентификатор пользователя
    uid = None
    if args:
        first = args[0]
        # Если передан объект строки результата
        try:
            if hasattr(first, '__getitem__') and 'user_id' in first:
                uid = first['user_id']
            elif isinstance(first, int):
                uid = first
        except Exception:
            pass
    if uid is None:
        uid = kwargs.get('current_user_id') or kwargs.get('user_id')
    return _db.get_profile(uid)

def update_profile_field(user_id: int, field: str, value):
    return _db.update_profile_field(user_id, field, value)

def user_liked(user_id: int, liked_user_id: int) -> bool:
    return _db.user_liked(user_id, liked_user_id)

def get_liked_by(user_id: int) -> list[dict]:
    return _db.get_liked_by(user_id)

def add_like(user_id: int,
             liked_user_id: int,
             message: str | None = None,
             amount: int = 0) -> bool:
    return _db.add_like(user_id, liked_user_id, message, amount)

def add_match(user_id: int, match_id: int):
    return _db.add_match(user_id, match_id)

def get_matches(user_id: int) -> list[dict]:
    return _db.get_matches(user_id)

def get_next_profile(*args, **kwargs) -> dict | None:
    return _db.get_next_profile(
        current_user_id=kwargs.get('current_user_id'),
        current_gender=kwargs.get('current_gender'),
        current_preference=kwargs.get('current_preference')
    )

def add_dislike(user_id: int, disliked_user_id: int):
    return _db.add_dislike(user_id, disliked_user_id)

def user_disliked(user_id: int, disliked_user_id: int) -> bool:
    return _db.user_disliked(user_id, disliked_user_id)

def get_all_profiles_sorted_by_balance() -> list[dict]:
    return _db.get_all_profiles_sorted_by_balance()

def change_balance(user_id: int, amount: int):
    return _db.change_balance(user_id, amount)

def award_given_like(user_id: int):
    return _db.award_given_like(user_id)

def award_given_dislike(user_id: int):
    return _db.award_given_dislike(user_id)

def award_received_like(user_id: int):
    return _db.award_received_like(user_id)

def award_received_dislike(user_id: int):
    return _db.award_received_dislike(user_id)

def sleep_profile(user_id: int):
    return _db.sleep_profile(user_id)
