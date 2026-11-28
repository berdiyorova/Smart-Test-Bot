import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://berdiyorova.alwaysdata.net")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEB_SERVER_HOST = os.environ.get("IP", "::")
WEB_SERVER_PORT = int(os.environ.get("PORT", 8080))