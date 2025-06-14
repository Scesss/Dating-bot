import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    YANDEX_GEOCODER_API_KEY = os.getenv("YANDEX_GEOCODER_API_KEY")
    # Add other configs later (database URL, etc.)
