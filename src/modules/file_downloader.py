import os
import logging
import magic
from telethon.tl.types import DocumentAttributeFilename
from config import DOWNLOAD_DIR
from utils.helpers import sanitize_name, get_dynamic_path

logger = logging.getLogger(__name__)

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

            file_path = os.path.join(DOWNLOAD_DIR, get_dynamic_path(file_name))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            await client.download_media(event.message, file_path)

            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)

            await event.reply(
                f"File downloaded: {file_name}\nType: {file_type}\nPath: {file_path}"
            )
            logger.info(f"File downloaded: {file_path}")
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            await event.reply("Sorry, there was an error downloading the file.")
    else:
        await event.reply("Please send a file to download.")
