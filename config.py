import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL = os.getenv("CHANNEL", "@ByteTunnel").strip()

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    ADMIN_ID = 0

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")

if ADMIN_ID == 0:
    raise RuntimeError("ADMIN_ID must be a numeric Telegram user ID")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DB_PATH = os.path.join(DATA_DIR, "toolbox.db")
