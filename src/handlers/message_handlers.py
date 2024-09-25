from telethon import events, Button
from modules.file_downloader import handle_file_download
from utils.bot_commands import get_commands_description
import logging

logger = logging.getLogger(__name__)


def register_message_handlers(client, plugins):
    @client.on(events.NewMessage)
    async def message_handler(event):
        # Ignore messages from bots or channels
        if event.sender is None or event.sender.bot or event.is_channel:
            logger.info(
                f"Ignoring message from bot or channel: {event.message.text[:50]}..."
            )
            return

        # Ignore messages with specific keywords or patterns
        ignore_keywords = [
            "Coolify Alert",
            "Bash Script Notification",
            "Coolify",
            "rp1",
        ]
        if any(keyword in event.raw_text for keyword in ignore_keywords):
            logger.info(f"Ignoring message with keyword: {event.message.text[:50]}...")
            return

        if event.document:
            await handle_file_download(event, client)
        elif not event.message.text.startswith("/"):
            await event.reply(
                "Welcome! I'm a multi-purpose bot. Use /start to see what I can do, or /help for a list of commands."
            )

    @client.on(events.CallbackQuery(pattern=r"list_commands"))
    async def list_commands_callback(event):
        await event.answer()
        await event.edit(
            "Here are the available commands:\n\n" + get_commands_description()
        )

    @client.on(events.CallbackQuery(pattern=r"zoho_auth"))
    async def zoho_auth_callback(event):
        await event.answer()
        await event.edit(
            "Please use the /zoho_auth command to start the authorization process."
        )
