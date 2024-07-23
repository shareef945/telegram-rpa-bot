import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Replace these with your own values
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_DIR = "/app/downloads"

# Create a new event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Create the client and connect
client = TelegramClient("bot", API_ID, API_HASH, loop=loop)

# Set to store processed message IDs
processed_messages = set()


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    logger.info(f"Received /start command from user {event.sender_id}")
    await event.reply("I'm ready to download files!")


@client.on(events.NewMessage)
async def download_file(event):
    if event.id in processed_messages:
        logger.info(f"Skipping already processed message {event.id}")
        return
    processed_messages.add(event.id)

    logger.info(f"Processing new message {event.id} from user {event.sender_id}")

    try:
        if event.document:
            sender = await event.get_sender()
            file = event.document

            attributes = event.document.attributes
            for attr in attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                    break
            else:
                file_name = "unknown_file"

            logger.info(f"Received file: {file_name} ({file.size} bytes)")

            if not os.path.exists(DOWNLOAD_DIR):
                os.makedirs(DOWNLOAD_DIR)
                logger.info(f"Created download directory: {DOWNLOAD_DIR}")

            file_path = os.path.join(DOWNLOAD_DIR, file_name)
            logger.info(f"File will be saved to: {file_path}")

            await event.reply(f"Starting download of {file_name} ({file.size} bytes)")

            await client.download_media(
                file,
                file_path,
                progress_callback=lambda current, total: progress_callback_func(
                    current, total, event, file_name
                ),
            )

            logger.info(f"File {file_name} downloaded successfully")
            await event.reply(f"File {file_name} downloaded successfully!")
        else:
            logger.info("Received message without document")
            await event.reply("Please send a file to download.")

    except Exception as e:
        logger.error(f"Error processing message {event.id}: {str(e)}", exc_info=True)
        await event.reply(f"An error occurred: {str(e)}")


async def progress_callback_func(current, total, event, file_name):
    percent = (current / total) * 100
    if int(percent) % 10 == 0:  # Update every 10%
        logger.info(f"Download progress for {file_name}: {percent:.1f}%")
    if int(percent) % 10 == 0:  # Update every 10%
        await event.reply(f"Downloaded {percent:.1f}% of {file_name}")


async def main():
    logger.info("Starting bot...")
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Bot is running")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    finally:
        logger.info("Closing client and event loop...")
        client.disconnect()
        loop.close()
        logger.info("Bot has been shut down")
