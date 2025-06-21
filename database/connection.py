import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def get_connection():
    """
    Устанавливает и возвращает соединение с PostgreSQL, используя переменные окружения.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "dating_db"),
        user=os.getenv("DB_USER", "dating_user"),
        password=os.getenv("DB_PASSWORD", "secret"),
        cursor_factory=RealDictCursor
    )