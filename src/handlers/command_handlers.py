from telethon import events, Button
from utils.bot_commands import get_commands_description
from utils.auth import require_auth
from config import USER_ROLES
import logging
import asyncio

logger = logging.getLogger(__name__)
WORKBOOK_CACHE = {}


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

        try:
            workbooks = await gsheets.list_workbooks()
            if workbooks:
                # Clear previous cache and store new workbook data
                WORKBOOK_CACHE.clear()

                # Create buttons with shorter callback data
                buttons = []
                for index, wb in enumerate(workbooks):
                    # Store workbook info in cache
                    cache_key = str(index)
                    WORKBOOK_CACHE[cache_key] = {"id": wb["id"], "name": wb["name"]}

                    # Create button with just the index as callback data
                    buttons.append(
                        [
                            Button.inline(
                                f"📊 {wb['name']}",
                                data=f"wb:{cache_key}",  # Much shorter callback data
                            )
                        ]
                    )

                await event.reply("📑 Select a workbook:", buttons=buttons)
            else:
                await event.reply(
                    "No spreadsheets found. Make sure to:\n"
                    "1. Share your spreadsheets with the service account email\n"
                    "2. Wait a few minutes after sharing"
                )
        except Exception as e:
            logger.error(f"Error listing workbooks: {str(e)}")
            await event.reply(f"Error: {str(e)}")

    @client.on(events.CallbackQuery(pattern=r"wb:(\d+)"))
    @require_auth("admin")
    async def handle_workbook_selection(event):
        try:
            # Extract workbook index from callback data
            wb_index = event.data.decode().split(":")[1]
            workbook = WORKBOOK_CACHE.get(wb_index)

            if not workbook:
                await event.edit("Session expired. Please run /list_workbooks again.")
                return

            gsheets = plugins.get("google_sheets")
            worksheets = await gsheets.list_worksheets(workbook["id"])

            if worksheets:
                # Create buttons for worksheets with shorter callback data
                buttons = [
                    [
                        Button.inline(
                            f"📋 {ws}", data=f"ws:{wb_index}:{i}"  # Short callback data
                        )
                    ]
                    for i, ws in enumerate(worksheets)
                ]

                # Store worksheet names in cache
                WORKBOOK_CACHE[wb_index]["worksheets"] = worksheets

                # Add back button
                buttons.append([Button.inline("🔙 Back", data="back_wb")])

                await event.edit(
                    f"📊 Workbook: **{workbook['name']}**\n\n" f"Select a worksheet:",
                    buttons=buttons,
                    parse_mode="md",
                )
            else:
                await event.edit(
                    f"No worksheets found in {workbook['name']}",
                    buttons=[[Button.inline("🔙 Back", data="back_wb")]],
                )
        except Exception as e:
            logger.error(f"Error in workbook selection: {str(e)}")
            await event.edit(f"An error occurred. Please try again.")

    @client.on(events.CallbackQuery(pattern=r"ws:(\d+):(\d+)"))
    @require_auth("admin")
    async def handle_worksheet_selection(event):
        try:
            # Extract data from callback
            _, wb_index, ws_index = event.data.decode().split(":")
            workbook = WORKBOOK_CACHE.get(wb_index)

            if not workbook or "worksheets" not in workbook:
                await event.edit("Session expired. Please run /list_workbooks again.")
                return

            worksheet_name = workbook["worksheets"][int(ws_index)]
            gsheets = plugins.get("google_sheets")

            # Get worksheet headers
            headers = await gsheets.get_headers(workbook["id"], worksheet_name)

            # Store the selection in the module
            gsheets.current_workbook = workbook["id"]
            gsheets.current_worksheet = worksheet_name

            # Create back buttons
            buttons = [
                [Button.inline("🔙 Back to Worksheets", data=f"wb:{wb_index}")],
                [Button.inline("🔙 Back to Workbooks", data="back_wb")],
            ]

            await event.edit(
                f"✅ Selected:\n"
                f"📊 Workbook: **{workbook['name']}**\n"
                f"📋 Worksheet: **{worksheet_name}**\n\n"
                f"📝 Headers: `{', '.join(headers)}`\n\n"
                f"Use `/add_row value1, value2, ...` to add data",
                buttons=buttons,
                parse_mode="md",
            )
        except Exception as e:
            logger.error(f"Error in worksheet selection: {str(e)}")
            await event.edit("An error occurred. Please try again.")

    @client.on(events.CallbackQuery(pattern=r"list_workbooks"))
    @require_auth("admin")
    async def handle_list_workbooks_callback(event):
        # Reuse the list_workbooks logic
        await list_workbooks(event)

    @client.on(events.CallbackQuery(pattern=r"back_wb"))
    @require_auth("admin")
    async def handle_back_to_workbooks(event):
        await list_workbooks(event)

    @client.on(events.NewMessage(pattern="/add_row"))
    @require_auth("admin")
    async def add_row(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return

        if not gsheets.current_workbook or not gsheets.current_worksheet:
            await event.reply(
                "No worksheet selected. Please select a worksheet first using /list_workbooks"
            )
            return

        try:
            # Extract values from the message
            message_text = event.message.text.split(maxsplit=1)[1]
            values = [v.strip() for v in message_text.split(",")]

            result = await gsheets.add_row(
                gsheets.current_workbook, gsheets.current_worksheet, values
            )

            await event.reply(
                f"✅ Row added successfully to worksheet: {gsheets.current_worksheet}"
            )
        except IndexError:
            await event.reply(
                "Please provide values separated by commas.\n"
                "Example: `/add_row value1, value2, value3`"
            )
        except Exception as e:
            await event.reply(f"❌ Error adding row: {str(e)}")
