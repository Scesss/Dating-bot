from database.connection import get_connection
import os
from dotenv import load_dotenv
from typing import Optional
from asyncpg import Record
import secrets
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
                referee_id BIGINT REFERENCES users(user_id),
                referral_code VARCHAR(16) UNIQUE,
                registered BOOLEAN DEFAULT FALSE,
                bonus_credited BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                user_id           BIGINT      NOT NULL,
                liked_user_id     BIGINT      NOT NULL,
                message           TEXT,
                amount            INTEGER     NOT NULL DEFAULT 0,
                seen_by_liked_user BOOLEAN    NOT NULL DEFAULT FALSE,
                created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (user_id, liked_user_id),
                FOREIGN KEY (user_id)       REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (liked_user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
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
                user_id        BIGINT      NOT NULL,
                match_id       BIGINT      NOT NULL,
                seen_by_user   BOOLEAN     NOT NULL DEFAULT FALSE,
                created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (user_id, match_id),
                FOREIGN KEY (user_id)  REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (match_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
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

    # ——— новые методы для непросмотренных лайков ———

    def get_unseen_likes_count(self, user_id: int) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM likes
            WHERE liked_user_id = %s
            AND seen_by_liked_user = FALSE
            """,
            (user_id,)
        )
        row = self.cursor.fetchone()
        # row теперь DictRow, и cnt — наш ключ
        return row["cnt"] or 0

    def mark_likes_seen(self, user_id: int) -> None:
        self.cursor.execute(
            "UPDATE likes "
            "   SET seen_by_liked_user = TRUE "
            " WHERE liked_user_id = %s AND seen_by_liked_user = FALSE",
            (user_id,)
        )
        self.conn.commit()

    # ——— новые методы для непросмотренных матчей ———

    def get_unseen_matches_count(self, user_id: int) -> int:
        self.cursor.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM matches
            WHERE user_id = %s
            AND seen_by_user = FALSE
            """,
            (user_id,)
        )
        row = self.cursor.fetchone()
        return row["cnt"] or 0

    def mark_matches_seen(self, user_id: int) -> None:
        self.cursor.execute(
            "UPDATE matches "
            "   SET seen_by_user = TRUE "
            " WHERE user_id = %s AND seen_by_user = FALSE",
            (user_id,)
        )
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
        """Кто лайкнул меня: возвращаем профиль + текст и сумму лайка."""
        self.cursor.execute("""
            SELECT
            u.user_id,
            u.name,
            u.age,
            u.gender,
            u.looking_for,
            u.balance,
            u.city,
            u.bio,
            u.photo_id,
            l.message   AS like_message,
            l.amount    AS like_amount,
            ROUND(
                (6371 * acos(
                    cos(radians(me.lat)) *
                    cos(radians(u.lat)) *
                    cos(radians(u.lon) - radians(me.lon)) +
                    sin(radians(me.lat)) *
                    sin(radians(u.lat))
                ))::numeric
            , 1
            )::double precision AS distance_km
            FROM likes l
            JOIN users u  ON l.user_id        = u.user_id
            JOIN users me ON me.user_id       = l.liked_user_id
            WHERE l.liked_user_id = %(user_id)s
        """, {"user_id": user_id})
        return [dict(row) for row in self.cursor.fetchall()]

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
        """Мои матчи: возвращаем профиль + исходный message/amount лайка."""
        self.cursor.execute(
            """
            SELECT
              u.*,
              l.message   AS like_message,
              l.amount    AS like_amount
            FROM users u
            JOIN matches m 
              ON m.match_id = u.user_id
             AND m.user_id = %s
            LEFT JOIN likes l
              ON l.user_id       = u.user_id
             AND l.liked_user_id = %s
            """,
            (user_id, user_id)
        )
        return [dict(row) for row in self.cursor.fetchall()]

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
            AND p.user_id NOT IN (
                SELECT disliked_user_id FROM dislikes WHERE user_id = %(current_user_id)s
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

    def get_user_rank(self, user_id: int) -> int:
        """
        Возвращает место пользователя в списке всех анкет,
        отсортированных по полю balance DESC.
        """
        # Получаем список всех user_id в порядке убывания баланса
        profiles = self.get_all_profiles_sorted_by_balance()
        for idx, prof in enumerate(profiles):
            if prof["user_id"] == user_id:
                return idx + 1
        # Если вдруг нет в списке — поместим в самый конец
        return len(profiles) + 1

    def insert_referral(self, referrer_id: int, referee_id: int) -> None:
        """Вставляет новую запись о рекомендации, если её ещё нет"""
        self.cursor.execute(
            "INSERT INTO referrals(referrer_id, referee_id) VALUES (%s, %s) "
            "ON CONFLICT (referee_id) DO NOTHING", (referrer_id, referee_id)
        )
        self.cursor.connection.commit()

    def mark_registered(self, code: str, referee_id: int) -> None:
        """
        Когда новый пользователь зашёл по коду,
        находим запись с referral_code=code и
        заполняем в ней referee_id + registered = TRUE
        """
        self.cursor.execute(
            """
            UPDATE referrals
            SET referee_id = %s, registered = TRUE
            WHERE referral_code = %s
              AND referee_id IS NULL
            """,
            (referee_id, code)
        )
        self.cursor.connection.commit()

    def get_pending_referral(self, referee_id: int) -> Optional[Record]:
        """
        Возвращает запись реферала, у которого registered=TRUE и bonus_credited=FALSE.
        """
        row = self.cursor.fetchrow(
            """
            SELECT id, referrer_id, referee_id
            FROM referrals
            WHERE referee_id = $1
              AND registered = TRUE
              AND bonus_credited = FALSE
            """, referee_id
        )
        # logger.debug(f"Pending referral lookup for referee_id={referee_id}: {row}")
        return row

    def mark_bonus_credited(self, referral_id: int) -> None:
        """Помечает запись реферала как получившего бонус."""
        self.cursor.execute(
            """
            UPDATE referrals
            SET bonus_credited = TRUE
            WHERE id = $1 AND bonus_credited = FALSE
            """, referral_id
        )
        # logger.debug(f"Referral bonus_credited set for id={referral_id}")

    def generate_referral_code(self) -> str:
        """Генерирует уникальный код для реферальной ссылки"""
        while True:
            code = secrets.token_urlsafe(8)
            self.cursor.execute(
                "SELECT 1 FROM referrals WHERE referral_code = %s", (code,)
            )
            if not self.cursor.fetchone():
                return code

    def ensure_referral_code(self, referrer_id: int) -> str:
        """Возвращает существующий код или создаёт новый и сохраняет его в referrals.referral_code"""
        # Проверяем, есть ли уже код для этого пригласившего
        self.cursor.execute(
            "SELECT referral_code FROM referrals WHERE referrer_id = %s AND referee_id IS NULL",
            (referrer_id,)
        )
        row = self.cursor.fetchone()
        code = None
        if row and isinstance(row, dict):
            code = row.get('referral_code')
        elif row:
            code = row[0]
        if code:
            return code
        # Генерируем новый код и сохраняем запись
        code = self.generate_referral_code()
        self.cursor.execute(
            "INSERT INTO referrals(referrer_id, referral_code) VALUES (%s, %s)",
            (referrer_id, code)
        )
        self.cursor.connection.commit()
        return code

    def get_user_id_by_referral_code(self, code: str) -> Optional[int]:
        """Ищет user_id по переданному коду"""
        self.cursor.execute(
            "SELECT user_id FROM users WHERE referral_code = %s", (code,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def check_and_credit_referral(self, referee_id: int) -> None:
        """Проверяет и, если условия выполнены, начисляет бонусы рефералу и рефереру"""
        # Получаем запись с невыданным бонусом
        self.cursor.execute(
            "SELECT id, referrer_id FROM referrals "
            "WHERE referee_id = %s AND registered = TRUE AND bonus_credited = FALSE",
            (referee_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            return
        referral_id, referrer_id = row

        # Получаем количество лайков
        self.cursor.execute(
            "SELECT likes_count FROM users WHERE user_id = %s", (referee_id,)
        )
        likes_row = self.cursor.fetchone()
        likes = likes_row[0] if likes_row else 0
        if likes < 10:
            return

        # Начисляем гемы (предполагается, что метод credit_gems синхронный)
        self.cursor.credit_gems(referrer_id, 5000)
        self.cursor.credit_gems(referee_id, 5000)

        # Помечаем бонус выданным
        self.cursor.execute(
            "UPDATE referrals SET bonus_credited = TRUE WHERE id = %s", (referral_id,)
        )
        self.cursor.connection.commit()

    def update_like_counters(self, sender_id, receiver_id):
        # Open a cursor and execute the necessary queries
        with self.cursor.connection() as cur:
            # Increment the sender's "likes_given"
            cur.execute("UPDATE users SET likes_given = likes_given + 1 WHERE id = %s", (sender_id,))
            # Increment the receiver's "likes_received"
            cur.execute("UPDATE users SET likes_received = likes_received + 1 WHERE id = %s", (receiver_id,))
            self.cursor.connection.commit()
            # Optionally, fetch the new counts to return
            cur.execute("SELECT likes_given FROM users WHERE id = %s", (sender_id,))
            new_sender = cur.fetchone()[0]
            cur.execute("SELECT likes_received FROM users WHERE id = %s", (receiver_id,))
            new_receiver = cur.fetchone()[0]
            return new_sender, new_receiver

    def count_successful_referrals(self, referrer_id: int) -> int:
        """
        Считает количество успешно выполненных рекомендаций с выданным бонусом.
        Поддерживает как tuple‐, так и dict‐курсор.
        """
        # Делаем явный алиас колонки для удобства
        self.cursor.execute(
            "SELECT COUNT(*) AS cnt "
            "FROM referrals "
            "WHERE referrer_id = %s AND bonus_credited = TRUE",
            (referrer_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            return 0

        # Если курсор возвращает dict — вытаскиваем по ключу 'cnt'
        if isinstance(row, dict):
            return row.get('cnt', 0)

        # Иначе считаем, что это tuple/list — первый элемент
        try:
            return row[0]
        except (IndexError, KeyError, TypeError):
            return 0

    def get_referrer_by_code(self, code: str) -> Optional[int]:
        """Ищем referrer_id по коду в referrals."""
        self.cursor.execute(
            "SELECT referrer_id FROM referrals WHERE referral_code = %s",
            (code,)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def generate_referral_code(self) -> str:
        """Генерирует уникальный код для реферальной ссылки"""
        while True:
            code = secrets.token_urlsafe(8)
            self.cursor.execute(
                "SELECT 1 FROM referrals WHERE referral_code = %s", (code,)
            )
            if not self.cursor.fetchone():
                return code

    def ensure_referral_code(self, referrer_id: int) -> str:
        """Возвращает существующий код или создаёт новый и сохраняет его в referrals.referral_code"""
        # Проверяем, есть ли уже код для этого пригласившего
        self.cursor.execute(
            "SELECT referral_code FROM referrals WHERE referrer_id = %s AND referee_id IS NULL",
            (referrer_id,)
        )
        row = self.cursor.fetchone()
        code = None
        if row and isinstance(row, dict):
            code = row.get('referral_code')
        elif row:
            code = row[0]
        if code:
            return code
        # Генерируем новый код и сохраняем запись
        code = self.generate_referral_code()
        self.cursor.execute(
            "INSERT INTO referrals(referrer_id, referral_code) VALUES (%s, %s)",
            (referrer_id, code)
        )
        self.cursor.connection.commit()
        return code

    def process_referral(self, referral_code: str, referee_id: int) -> bool:
        """
        Обрабатывает переход по реферальной ссылке:
        - Находит запись в referrals по referral_code и referee_id IS NULL
        - Если найдена и referrer_id != referee_id, устанавливает referee_id и registered = TRUE
        - Возвращает True, если запись обновлена, иначе False
        """
        self.cursor.execute(
            "SELECT id, referrer_id FROM referrals WHERE referral_code = %s AND referee_id IS NULL",
            (referral_code,)
        )
        row = self.cursor.fetchone()
        if not row:
            return False
        if isinstance(row, dict):
            referral_id = row.get("id")
            referrer_id = row.get("referrer_id")
        else:
            referral_id, referrer_id = row
        if referrer_id == referee_id:
            return False
        self.cursor.execute(
            "UPDATE referrals SET referee_id = %s, registered = TRUE WHERE id = %s",
            (referee_id, referral_id)
        )
        self.connection.commit()
        return True


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

def add_like(user_id: int,
             liked_user_id: int,
             message: str | None = None,
             amount: int = 0) -> bool:
    return _db.add_like(user_id, liked_user_id, message, amount)

def add_match(user_id: int, match_id: int):
    return _db.add_match(user_id, match_id)

def get_next_profile(*args, **kwargs) -> dict | None:
    return _db.get_next_profile(
        current_user_id=kwargs.get('current_user_id'),
        current_gender=kwargs.get('current_gender'),
        current_preference=kwargs.get('current_preference'),
        current_lat= kwargs.get('current_lat'),
        current_lon= kwargs.get('current_lon')
    )

def add_dislike(user_id: int, disliked_user_id: int):
    return _db.add_dislike(user_id, disliked_user_id)

def user_disliked(user_id: int, disliked_user_id: int) -> bool:
    return _db.user_disliked(user_id, disliked_user_id)

def get_all_profiles_sorted_by_balance() -> list[dict]:
    return _db.get_all_profiles_sorted_by_balance()

def change_balance(user_id: int, amount: int):
    return _db.change_balance(user_id, amount)

def sleep_profile(user_id: int):
    return _db.sleep_profile(user_id)

def get_unseen_likes_count(user_id: int) -> int:
    return _db.get_unseen_likes_count(user_id)

def mark_likes_seen(user_id: int) -> None:
    _db.mark_likes_seen(user_id)

def get_unseen_matches_count(user_id: int) -> int:
    return _db.get_unseen_matches_count(user_id)

def mark_matches_seen(user_id: int) -> None:
    _db.mark_matches_seen(user_id)

def get_liked_by(user_id: int) -> list[dict]:
    return _db.get_liked_by(user_id)

def get_matches(user_id: int) -> list[dict]:
    return _db.get_matches(user_id)

def get_user_rank(user_id: int) -> int:
    return _db.get_user_rank(user_id)

def get_pending_referral(self, referee_id: int) -> Optional[Record]:
    return _db.get_pending_referral(referee_id)

def mark_bonus_credited(self, referral_id: int) -> None:
    return _db.mark_bonus_credited(referral_id)

def count_successful_referrals(referrer_id: int) -> int:
    return _db.count_successful_referrals(referrer_id)

def update_like_counters(sender_id, receiver_id):
    return _db.update_like_counters(sender_id, receiver_id)

def generate_referral_code() -> str:
    return _db.generate_referral_code()

def get_user_id_by_referral_code(code: str) -> Optional[int]:
    return _db.get_user_id_by_referral_code(code)

def check_and_credit_referral(referee_id: int) -> None:
    return _db.check_and_credit_referral(referee_id)

def insert_referral(referrer_id: int, referee_id: int) -> None:
    # """Вставляет новую запись о рекомендации"""
    return _db.insert_referral(referrer_id, referee_id)

def ensure_referral_code(referrer_id: int) -> str:
    return _db.ensure_referral_code(referrer_id)

def get_referrer_by_code(code: str) -> Optional[int]:
    return _db.get_referrer_by_code(code)

def mark_registered(code: str, referee_id: int) -> None:
    return _db.mark_registered(code, referee_id)

def process_referral(referral_code: str, referee_id: int) -> bool:
    return _db.process_referral(referral_code, referee_id)

db = _db