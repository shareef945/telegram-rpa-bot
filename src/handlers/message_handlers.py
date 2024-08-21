from telethon import events
from modules.file_downloader import handle_file_download


def register_message_handlers(client):
    @client.on(events.NewMessage)
    async def message_handler(event):
        if event.document:
            await handle_file_download(event, client)
        else:
            # Handle other types of messages or commands
            await event.reply(
                "I can handle file downloads and create invoices. Use /start for more information."
            )
