import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = "/app/downloads"
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_ORGANIZATION_ID = os.getenv("ZOHO_ORGANIZATION_ID")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
USER_ROLES = {
    int(user_id): role
    for user_id, role in [
        user_role.split(":")
        for user_role in os.getenv("USER_ROLES", "").split(",")
        if ":" in user_role
    ]
}
