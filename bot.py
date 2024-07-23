import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Use environment variables for credentials
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Create the client and connect
client = TelegramClient("bot", API_ID, API_HASH, loop=loop)


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.reply("I'm ready to download files!")


@client.on(events.NewMessage)
async def download_file(event):
    try:
        if event.document:
            sender = await event.get_sender()
            file = event.document

            # Default file name if none is found
            file_name = "unknown_file"
            attributes = event.document.attributes
            for attr in attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                    break

            if not os.path.exists(DOWNLOAD_DIR):
                os.makedirs(DOWNLOAD_DIR)

            file_path = os.path.join(DOWNLOAD_DIR, file_name)

            await event.reply(f"Starting download of {file_name} ({file.size} bytes)")

            # ... rest of your code ...

        else:
            await event.reply("Please send a file to download.")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        await event.reply(f"An error occurred: {str(e)}")


async def progress_callback_func(current, total, event, file_name):
    percent = (current / total) * 100
    if int(percent) % 10 == 0:  # Update every 10%
        await event.reply(f"Downloaded {percent:.1f}% of {file_name}")


async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Bot is running...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(client.disconnect())
        loop.close()
