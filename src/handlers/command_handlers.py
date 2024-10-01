from telethon import events
from utils.bot_commands import get_commands_description
from utils.auth import require_auth
from config import USER_ROLES
import logging
import asyncio


def register_command_handlers(client, plugins):

    @client.on(events.NewMessage(pattern="/help"))
    async def help_command(event):
        user_id = event.sender_id
        user_role = USER_ROLES.get(user_id, "guest")
        commands = get_commands_description(user_role)
        await event.reply(
            "Here are a list of things I can do!\n\n"
            "• Plex Server Media Download: Send me a movie or tv-show, access it via SAI's Plex server or NAS. \n"
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

    @client.on(events.NewMessage(pattern="/gsheets_auth"))
    @require_auth("admin")
    async def gsheets_auth(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return
        asyncio.create_task(gsheets.start_oauth_server())
        auth_url = gsheets.generate_auth_url()
        await event.reply(
            f"Please visit this URL to authorize the application: {auth_url}\n\n"
            "After authorization, you'll be redirected to a local page. "
            "Once you see the success message, you can close the browser tab."
        )

    @client.on(events.NewMessage(pattern="/gsheets_code"))
    @require_auth("admin")
    async def gsheets_code(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return
        try:
            code = event.message.text.split(maxsplit=1)[1]
            if gsheets.complete_auth(code):
                await event.reply(
                    "Authorization successful! You can now use Google Sheets commands."
                )
            else:
                await event.reply(
                    "Authorization failed. Please try again with /gsheets_auth."
                )
        except IndexError:
            await event.reply(
                "Please provide the authorization code after the /gsheets_code command."
            )
        except Exception as e:
            await event.reply(
                f"An error occurred: {str(e)}. Please try again with /gsheets_auth."
            )

    @client.on(events.NewMessage(pattern="/list_workbooks"))
    @require_auth("admin")
    async def list_workbooks(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return
        if not gsheets.load_credentials():
            await event.reply("Please authorize the bot first using /gsheets_auth")
            return
        workbooks = await gsheets.list_workbooks()
        if workbooks:
            workbook_list = "\n".join(
                [f"{i+1}. {wb['name']}" for i, wb in enumerate(workbooks)]
            )
            await event.reply(
                f"Available workbooks:\n{workbook_list}\n\nUse /select_workbook <number> to choose a workbook."
            )
        else:
            await event.reply("No workbooks found.")

    @client.on(events.NewMessage(pattern="/select_workbook"))
    @require_auth("admin")
    async def select_workbook(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return
        try:
            workbook_index = int(event.message.text.split()[1]) - 1
            workbooks = await gsheets.list_workbooks()
            selected_workbook = workbooks[workbook_index]
            worksheets = await gsheets.list_worksheets(selected_workbook["id"])
            worksheet_list = "\n".join(
                [f"{i+1}. {ws}" for i, ws in enumerate(worksheets)]
            )
            await event.reply(
                f"Selected workbook: {selected_workbook['name']}\n\nAvailable worksheets:\n{worksheet_list}\n\nUse /select_worksheet <number> to choose a worksheet."
            )
        except (IndexError, ValueError):
            await event.reply("Please provide a valid workbook number.")

    @client.on(events.NewMessage(pattern="/select_worksheet"))
    @require_auth("admin")
    async def select_worksheet(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return
        try:
            worksheet_index = int(event.message.text.split()[1]) - 1
            workbooks = await gsheets.list_workbooks()
            selected_workbook = workbooks[0]  # Assuming the first workbook is selected
            worksheets = await gsheets.list_worksheets(selected_workbook["id"])
            selected_worksheet = worksheets[worksheet_index]
            headers = await gsheets.get_headers(
                selected_workbook["id"], selected_worksheet
            )
            header_list = ", ".join(headers)
            await event.reply(
                f"Selected worksheet: {selected_worksheet}\n\nHeaders: {header_list}\n\nUse /add_row <value1>,<value2>,... to add a new row."
            )
        except (IndexError, ValueError):
            await event.reply("Please provide a valid worksheet number.")

    @client.on(events.NewMessage(pattern="/add_row"))
    @require_auth("admin")
    async def add_row(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return
        try:
            values = event.message.text.split(maxsplit=1)[1].split(",")
            workbooks = await gsheets.list_workbooks()
            selected_workbook = workbooks[0]  # Assuming the first workbook is selected
            worksheets = await gsheets.list_worksheets(selected_workbook["id"])
            selected_worksheet = worksheets[
                0
            ]  # Assuming the first worksheet is selected
            result = await gsheets.add_row(
                selected_workbook["id"], selected_worksheet, values
            )
            await event.reply(
                f"Row added successfully. Updated range: {result['updates']['updatedRange']}"
            )
        except IndexError:
            await event.reply(
                "Please provide values for the new row, separated by commas."
            )
        except Exception as e:
            await event.reply(f"An error occurred: {str(e)}")
