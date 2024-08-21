import asyncio
import logging
from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN
from handlers.command_handlers import register_command_handlers
from handlers.message_handlers import register_message_handlers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    client = TelegramClient("bot", API_ID, API_HASH)

    register_command_handlers(client)
    register_message_handlers(client)

    try:
        await client.start(bot_token=BOT_TOKEN)
        logger.info("Bot started successfully")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
