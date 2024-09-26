from telethon import events
from utils.bot_commands import get_commands_description
from utils.auth import require_auth
from config import USER_ROLES
import logging


def register_command_handlers(client, plugins):

    @client.on(events.NewMessage(pattern="/help"))
    async def help_command(event):
        user_id = event.sender_id
        user_role = USER_ROLES.get(user_id, "guest")
        commands = get_commands_description(user_role)
        await event.reply(
            "Here are a list of things I can do!\n\n"
            "• Media Downloads: Send me a Movie, or TV show.\n"
            "• Zoho Books Integration: Create invoices and manage customers.\n"
            "• Custom API Interactions.\n\n"
            f"Your user ID: {user_id}\nYour role: {user_role}\n\n"
            f"Here are the commands you can use:\n\n{commands}"
        )

    @client.on(events.NewMessage(pattern="/zoho_auth"))
    @require_auth("admin")
    async def zoho_auth(event):
        zoho = plugins.get("zoho_invoicing")
        if not zoho:
            await event.reply("Zoho integration is not available.")
            return
        auth_url = zoho.generate_auth_url()
        await event.reply(
            f"Please visit this URL to authorize the application: {auth_url}\n\n"
            "After authorization, you'll be redirected to a page. "
            "Copy the entire URL from your browser's address bar and "
            "send it to me using the /zoho_code command."
        )

    @client.on(events.NewMessage(pattern="/zoho_code"))
    @require_auth("admin")
    async def zoho_code(event):
        zoho = plugins.get("zoho_invoicing")
        if not zoho:
            await event.reply("Zoho integration is not available.")
            return
        try:
            full_url = event.message.text.split(maxsplit=1)[1]
            code = full_url.split("code=")[1].split("&")[0]
            if await zoho.get_tokens(code):
                await event.reply(
                    "Authorization successful! You can now use Zoho Books commands."
                )
            else:
                await event.reply(
                    "Authorization failed. Please try again with /zoho_auth."
                )
        except IndexError:
            await event.reply(
                "Please provide the full URL after the /zoho_code command."
            )
        except Exception as e:
            await event.reply(
                f"An error occurred: {str(e)}. Please try again with /zoho_auth."
            )

    @client.on(events.NewMessage(pattern="/create_invoice"))
    @require_auth("admin")
    async def create_invoice(event):
        zoho = plugins.get("zoho_invoicing")
        if not zoho:
            await event.reply("Zoho integration is not available.")
            return
        if not zoho.access_token:
            await event.reply("Please authorize the bot first using /zoho_auth")
            return

        try:
            # For demonstration, we're using hardcoded values
            customer_id = "123456"
            items = [{"item_id": "item1", "rate": 100, "quantity": 1}]
            invoice = await zoho.create_invoice(customer_id, items)
            if invoice:
                await event.reply(
                    f"Invoice created successfully. Invoice ID: {invoice['invoice_id']}"
                )
            else:
                await event.reply("Failed to create invoice. Please try again later.")
        except Exception as e:
            await event.reply(f"An error occurred: {str(e)}")

    @client.on(events.NewMessage(pattern="/list_customers"))
    @require_auth("admin")
    async def list_customers(event):
        zoho = plugins.get("zoho_invoicing")
        if not zoho:
            await event.reply("Zoho integration is not available.")
            return
        if not zoho.access_token:
            await event.reply("Please authorize the bot first using /zoho_auth")
            return

        try:
            customers = await zoho.get_customers()
            logging.info(f"Fetched customers: {customers}")  # Log the response

            if customers:
                customer_list = "\n".join(
                    [f"{c['contact_name']}" for c in customers[:10]]
                )
                await event.reply(f"Here are the first 10 customers:\n{customer_list}")
            else:
                await event.reply("Failed to fetch customers. Please try again later.")
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")  # Log the error
            await event.reply(f"An error occurred: {str(e)}")

    @client.on(events.NewMessage(pattern="/my_id"))
    async def my_id_command(event):
        user_id = event.sender_id
        await event.reply(f"Your Telegram user ID is: {user_id}")
