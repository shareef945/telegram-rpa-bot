import os
import logging
import magic
from telethon.tl.types import DocumentAttributeFilename
from config import DOWNLOAD_DIR
from utils.helpers import get_dynamic_path
from time import time

logger = logging.getLogger(__name__)


async def progress_callback(current, total, event, file_name, start_time):
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


async def handle_file_download(event, client):
    if event.document:
        try:
            attributes = event.document.attributes
            for attr in attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    file_name = attr.file_name
                    break
            else:
                file_name = "unknown_file"

            file_size = event.document.size
            logger.info(f"Received file: {file_name} ({file_size} bytes)")
            await event.reply(
                f"Starting download of {file_name} ({file_size} bytes). Please wait."
            )

            relative_path = get_dynamic_path(file_name)
            file_path = os.path.join(DOWNLOAD_DIR, relative_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            start_time = time()
            await client.download_media(
                event.message,
                file_path,
                progress_callback=lambda current, total: progress_callback(
                    current, total, event, file_name, start_time
                ),
            )

            # Set correct file permissions after download
            os.chmod(file_path, 0o644)

            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)

            if not file_type.startswith("video/"):
                logger.warning(f"File type mismatch. MIME type: {file_type}")

            logger.info(f"File downloaded: {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            await event.reply("Sorry, there was an error downloading the file.")
    else:
        await event.reply("Please send a file to download.")
