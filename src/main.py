import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from config import API_ID, API_HASH, BOT_TOKEN, USER_ROLES
from handlers import register_handlers
from plugins import load_plugins

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    client = TelegramClient("bot", API_ID, API_HASH)

    try:
        plugins = load_plugins()
        register_handlers(client, plugins)

        while True:
            try:
                await client.start(bot_token=BOT_TOKEN)
                logger.info("Bot started successfully")
                break  # Exit the loop if successful
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(
                    f"Rate limited. Waiting {wait_time} seconds before retrying..."
                )
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Failed to start bot: {str(e)}")
                raise

        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
    finally:
        await client.disconnect()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
