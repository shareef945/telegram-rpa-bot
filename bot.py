import os
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
from time import time
from collections import deque
import re
import magic

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

# Message deduplication
recent_messages = deque(maxlen=100)


def sanitize_name(name):
    # Replace spaces with hyphens and convert to lowercase
    # Remove any characters that aren't alphanumeric, hyphens, or underscores
    return re.sub(r"[^\w\-]", "", name.replace(" ", "-")).lower()


def get_dynamic_path(file_name):
    name, extension = os.path.splitext(file_name)

    # Check if it's a TV show
    tv_match = re.search(r"(.*?)S(\d+)E(\d+)", name, re.IGNORECASE)
    if tv_match:
        show_name = sanitize_name(tv_match.group(1).strip())
        season = int(tv_match.group(2))
        episode = int(tv_match.group(3))
        return os.path.join(
            "tv-shows", show_name, f"s{season}", f"e{episode}{extension.lower()}"
        )
    else:
        # If not a TV show, assume it's a movie
        year_match = re.search(r"\.(\d{4})\.", name)
        if year_match:
            year = year_match.group(1)
        else:
            year = "unknown-year"
        movie_name = sanitize_name(name)
        return os.path.join("movies", year, f"{movie_name}{extension.lower()}")


async def progress_callback_func(current, total, event, file_name, start_time):
    percent = (current / total) * 100

    # Log progress when download starts and completes
    if current == 0 or current == total:
        logger.info(f"Download progress for {file_name}: {percent:.1f}%")

    # Update user when download starts and completes
    if current == 0:
        await event.reply(f"Starting download of {file_name}...")
    elif current == total:
        elapsed_time = time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        await event.reply(
            f"Download of {file_name} completed in {minutes} minute(s) and {seconds} second(s)."
        )


async def process_message(event):
    logger.info(f"Processing message {event.id} from user {event.sender_id}")

    try:
        # Check if the message is a Coolify deployment notification
        if event.message and (
            "New version successfully deployed of" in event.message.text
            or "Coolify: Deployment failed of" in event.message.text
        ):
            logger.info(f"Ignoring Coolify deployment message: {event.message.text}")
            return  # Skip processing for Coolify deployment messages

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
            await event.reply(
                f"Starting download of {file_name} ({file.size} bytes). Please wait."
            )
            logger.info(f"Starting download for {file_name}")
            # Get the dynamic path for the file
            relative_path = get_dynamic_path(file_name)
            full_path = os.path.join(DOWNLOAD_DIR, relative_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            start_time = time()
            await client.download_media(
                file,
                full_path,
                progress_callback=lambda current, total: progress_callback_func(
                    current, total, event, file_name, start_time
                ),
            )

            # Set correct file permissions after download
            os.chmod(full_path, 0o644)

            # Verify file type
            file_type = magic.from_file(full_path, mime=True)
            if not file_type.startswith("video/"):
                logger.warning(f"File type mismatch. MIME type: {file_type}")

        else:
            logger.info("Received message without document")
            await event.reply("Please send a file to download.")

    except Exception as e:
        logger.error(f"Error processing message {event.id}: {str(e)}", exc_info=True)
        await event.reply(f"An error occurred: {str(e)}")


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    logger.info(f"Received /start command from user {event.sender_id}")
    await event.reply("I'm ready to download files!")


@client.on(events.NewMessage)
async def message_handler(event):
    if event.id in recent_messages:
        logger.info(f"Skipping duplicate message {event.id}")
        return

    recent_messages.append(event.id)

    try:
        await process_message(event)
    except Exception as e:
        logger.error(f"Error processing message {event.id}: {str(e)}", exc_info=True)


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
