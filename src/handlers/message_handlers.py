from telethon import events, Button
from modules.file_downloader import handle_file_download
from utils.bot_commands import get_commands_description
import logging
from handlers.command_handlers import WORKBOOK_CACHE

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
            "✅ Payment recorded successfully",
        ]
        if any(keyword in event.raw_text for keyword in ignore_keywords):
            logger.info(f"Ignoring message with keyword: {event.message.text[:50]}...")
            return

        # Check if we're expecting a payment amount
        if hasattr(client, "expecting_payment") and client.expecting_payment():
            return

        # Only show welcome message for non-command, non-file, non-reply messages
        # AND when we're not expecting a payment amount
        if (
            not event.document
            and not event.message.text.startswith("/")
            and not event.message.is_reply
            and not WORKBOOK_CACHE.get("expecting_amount", False)  # Add this condition
        ):
            await event.reply(
                "Welcome to SAI Technology's Robotics Process Automation (RPA) service!  type /help to see what i am capable of"
            )

    @client.on(events.CallbackQuery(pattern=r"list_commands"))
    async def list_commands_callback(event):
        await event.answer()
        await event.edit(
            "Here are the available commands:\n\n" + get_commands_description()
        )
