from telethon import events, Button
from utils.bot_commands import get_commands_description
from utils.auth import require_auth
from config import USER_ROLES
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
WORKBOOK_CACHE = {}

PAYMENT_CONFIGS = {
    "sales_tracking": {
        "workbook_id": "1olamGPcDmnUUNDfWJI4wSugQm5-_osezxLzm7fWeEos",
        "worksheet_name": "Financial Data",
        "product_data": {
            "worksheet_name": "Product Information",
            "range": "A2:P",  # Adjust this range to include all needed columns
            "columns": {
                "product_id": 2,  # Column C (index 1)
                "customer_name": 4,  # Column B (index 0)
                "weekly_installment": 13,  # Column D (index 2)
                "other_info": 3,  # Column E (index 3)
            },
        },
        "columns": {"product_id": 0, "amount": 2, "date": 3, "days_late": 4},
    }
}


async def handle_error(event, error, message="An error occurred"):
    logger.error(f"{message}: {str(error)}")
    await event.reply(f"❌ {message}: {str(error)}")


async def create_workbook_buttons(workbooks):
    WORKBOOK_CACHE.clear()
    return [
        [Button.inline(f"📊 {wb['name']}", data=f"wb:{i}")]
        for i, wb in enumerate(workbooks)
        if WORKBOOK_CACHE.update({str(i): {"id": wb["id"], "name": wb["name"]}}) or True
    ]


async def create_worksheet_buttons(workbook_index, worksheets):
    buttons = [
        [Button.inline(f"📋 {ws}", data=f"ws:{workbook_index}:{i}")]
        for i, ws in enumerate(worksheets)
    ]
    buttons.append([Button.inline("🔙 Back", data="back_wb")])
    return buttons


def register_command_handlers(client, plugins):
    @client.on(events.NewMessage(pattern="/help"))
    async def help_command(event):
        user_id = event.sender_id
        user_role = USER_ROLES.get(user_id, "guest")
        commands = get_commands_description(user_role)
        await event.reply(
            "Here are a list of things I can do!\n\n"
            "• Plex Server Media Download: Send me a movie or tv-show, access it via SAI's Plex server or NAS. \n"
            "• Google Sheets Input: Input data to selected google sheet\n"
            f"Your user ID: {user_id}\nYour role: {user_role}\n\n"
            f"Here are the commands you can use:\n\n{commands}"
        )

    @client.on(events.NewMessage(pattern="/my_id"))
    async def my_id_command(event):
        await event.reply(f"Your Telegram user ID is: {event.sender_id}")

    @client.on(events.NewMessage(pattern="/list_workbooks"))
    @require_auth("admin")
    async def list_workbooks(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return

        try:
            workbooks = await gsheets.list_workbooks()
            if not workbooks:
                await event.reply(
                    "No spreadsheets found. Make sure to:\n"
                    "1. Share your spreadsheets with the service account email\n"
                    "2. Wait a few minutes after sharing"
                )
                return

            buttons = await create_workbook_buttons(workbooks)
            await event.reply("📑 Select a workbook:", buttons=buttons)
        except Exception as e:
            await handle_error(event, e, "Error listing workbooks")

    @client.on(events.CallbackQuery(pattern=r"wb:(\d+)"))
    @require_auth("admin")
    async def handle_workbook_selection(event):
        try:
            wb_index = event.data.decode().split(":")[1]
            workbook = WORKBOOK_CACHE.get(wb_index)

            if not workbook:
                await event.edit("Session expired. Please run /list_workbooks again.")
                return

            gsheets = plugins.get("google_sheets")
            worksheets = await gsheets.list_worksheets(workbook["id"])

            if worksheets:
                WORKBOOK_CACHE[wb_index]["worksheets"] = worksheets
                buttons = await create_worksheet_buttons(wb_index, worksheets)
                await event.edit(
                    f"📊 Workbook: **{workbook['name']}**\n\nSelect a worksheet:",
                    buttons=buttons,
                    parse_mode="md",
                )
            else:
                await event.edit(
                    f"No worksheets found in {workbook['name']}",
                    buttons=[[Button.inline("🔙 Back", data="back_wb")]],
                )
        except Exception as e:
            await handle_error(event, e, "Error in workbook selection")

    @client.on(events.CallbackQuery(pattern=r"ws:(\d+):(\d+)"))
    @require_auth("admin")
    async def handle_worksheet_selection(event):
        try:
            _, wb_index, ws_index = event.data.decode().split(":")
            workbook = WORKBOOK_CACHE.get(wb_index)

            if not workbook or "worksheets" not in workbook:
                await event.edit("Session expired. Please run /list_workbooks again.")
                return

            worksheet_name = workbook["worksheets"][int(ws_index)]
            gsheets = plugins.get("google_sheets")
            headers = await gsheets.get_headers(workbook["id"], worksheet_name)

            gsheets.current_workbook = workbook["id"]
            gsheets.current_worksheet = worksheet_name

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
            await handle_error(event, e, "Error in worksheet selection")

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
            message_text = event.message.text.split(maxsplit=1)[1]
            values = [v.strip() for v in message_text.split(",")]
            await gsheets.add_row(
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
            await handle_error(event, e, "Error adding row")

    @client.on(events.NewMessage(pattern="/record_payment"))
    @require_auth("admin")
    async def record_payment(event):
        gsheets = plugins.get("google_sheets")
        if not gsheets:
            await event.reply("Google Sheets integration is not available.")
            return

        config = PAYMENT_CONFIGS["sales_tracking"]
        try:
            range_name = f"{config['product_data']['worksheet_name']}!{config['product_data']['range']}"
            rows = await gsheets.get_values(config["workbook_id"], range_name)

            if not rows:
                await event.reply("❌ No products found in the product sheet.")
                return

            buttons = []
            active_count = 0
            for row in rows:  # Remove the [:10] limit since we'll filter active ones
                if (
                    len(row) >= 15 and row[15].upper() == "TRUE"
                ):  # Check if product is active
                    if active_count >= 10:  # Only show first 10 active products
                        break

                    product_id = row[config["product_data"]["columns"]["product_id"]]
                    customer_name = row[
                        config["product_data"]["columns"]["customer_name"]
                    ]
                    weekly_installment = row[
                        config["product_data"]["columns"]["weekly_installment"]
                    ]

                    button_text = (
                        f"📦 {product_id} | {customer_name}\n"
                        f"💰 Weekly: {weekly_installment}"
                    )
                    buttons.append(
                        [Button.inline(button_text, data=f"payment_prod:{product_id}")]
                    )
                    active_count += 1

            if not buttons:
                await event.reply("❌ No active products found.")
                return

            if (
                len(
                    [
                        row
                        for row in rows
                        if len(row) >= 15 and row[14].upper() == "TRUE"
                    ]
                )
                > 10
            ):
                buttons.append([Button.inline("Next ➡️", data="payment_next:10")])

            await event.reply(
                "🧾 Record Payment\n\n" "Select a product from the list below:",
                buttons=buttons,
            )
        except Exception as e:
            await handle_error(event, e, "Error fetching products")

    @client.on(events.CallbackQuery(pattern=r"payment_prod:(.+)"))
    @require_auth("admin")
    async def handle_payment_product_selection(event):
        try:
            product_id = event.data.decode().split(":")[1]

            # Get product details
            config = PAYMENT_CONFIGS["sales_tracking"]
            gsheets = plugins.get("google_sheets")
            range_name = f"{config['product_data']['worksheet_name']}!{config['product_data']['range']}"
            rows = await gsheets.get_values(config["workbook_id"], range_name)

            product_details = None
            for row in rows:
                if row[config["product_data"]["columns"]["product_id"]] == product_id:
                    product_details = row
                    break

            if product_details:
                customer_name = product_details[
                    config["product_data"]["columns"]["customer_name"]
                ]
                weekly_installment = product_details[
                    config["product_data"]["columns"]["weekly_installment"]
                ]

                WORKBOOK_CACHE["temp_product"] = product_id
                WORKBOOK_CACHE["expecting_amount"] = True

                # Send a new message instead of editing
                await event.respond(
                    "🧾 Record Payment\n\n"
                    f"Customer: {customer_name}\n"
                    f"Product ID: {product_id}\n"
                    f"Weekly Installment: {weekly_installment}\n\n"
                    "Simply type the payment amount (e.g., 500)\n"
                    "Type 'cancel' to abort the operation."
                )
                # Delete the original message with buttons
                await event.delete()
            else:
                await event.edit("❌ Product details not found. Please try again.")

        except Exception as e:
            await handle_error(event, e, "Error in payment selection")

    @client.on(events.NewMessage())
    @require_auth("admin")
    async def handle_payment_amount(event):
        if not WORKBOOK_CACHE.get("expecting_amount"):
            return

        if event.message.text.lower() in ["/cancel", "cancel", "abort", "/abort"]:
            WORKBOOK_CACHE.pop("temp_product", None)
            WORKBOOK_CACHE.pop("expecting_amount", None)
            await event.reply(
                "❌ Payment recording cancelled. Use /record_payment to start over."
            )
            return

        try:
            amount = float(event.message.text)
            product_id = WORKBOOK_CACHE.get("temp_product")

            if not product_id:
                await event.reply("❌ Please start over with /record_payment")
                WORKBOOK_CACHE.pop("expecting_amount", None)
                return

            config = PAYMENT_CONFIGS["sales_tracking"]
            gsheets = plugins.get("google_sheets")
            today = datetime.now().strftime("%Y-%m-%d")
            days_late = await gsheets.calculate_days_late(product_id)

            # Create a list with the correct size and fill it with empty strings
            max_col = (
                max(config["columns"].values()) + 1
            )  # Add 1 because indices are 0-based
            row_data = [""] * max_col

            # Fill in the data
            row_data[config["columns"]["product_id"]] = product_id
            row_data[config["columns"]["amount"]] = str(amount)
            row_data[config["columns"]["date"]] = today
            row_data[config["columns"]["days_late"]] = str(days_late)

            await gsheets.append_row(
                config["workbook_id"], config["worksheet_name"], row_data
            )

            WORKBOOK_CACHE.pop("temp_product", None)
            WORKBOOK_CACHE.pop("expecting_amount", None)

            await event.reply(
                "✅ Payment recorded successfully!\n\n"
                f"📦 Product: {product_id}\n"
                f"💰 Amount: {amount}\n"
                f"📅 Date: {today}\n"
                f"⏰ Days Late: {days_late}\n\n"
                "Use /record_payment to record another payment"
            )
        except ValueError:
            await event.reply(
                "❌ Please enter a valid number (e.g., 500)\n\n"
                "Type 'cancel' to abort the operation, or try again with a valid number."
            )
        except Exception as e:
            WORKBOOK_CACHE.pop("temp_product", None)
            WORKBOOK_CACHE.pop("expecting_amount", None)
            await handle_error(event, e, "Error recording payment")
