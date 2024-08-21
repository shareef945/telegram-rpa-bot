from telethon import events
from modules.zoho_invoicing import ZohoInvoicing

zoho = ZohoInvoicing()


def register_command_handlers(client):
    @client.on(events.NewMessage(pattern="/zoho_auth"))
    async def zoho_auth(event):
        auth_url = zoho.generate_auth_url()
        await event.reply(
            f"Please visit this URL to authorize the application: {auth_url}\n\n"
            "After authorization, you'll be redirected to a page. "
            "Copy the entire URL from your browser's address bar and "
            "send it to me using the /zoho_code command."
        )

    @client.on(events.NewMessage(pattern="/zoho_code"))
    async def zoho_code(event):
        try:
            full_url = event.message.text.split(maxsplit=1)[1]
            code = full_url.split("code=")[1].split("&")[0]
            if await zoho.get_tokens(code):
                if zoho.refresh_token:
                    await event.reply(
                        "Authorization successful! You can now use Zoho Books commands."
                    )
                else:
                    await event.reply(
                        "Authorization partially successful. No refresh token received. "
                        "You may need to reauthorize more frequently. "
                        "You can use Zoho Books commands for now."
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
    async def create_invoice(event):
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
    async def list_customers(event):
        if not zoho.access_token:
            await event.reply("Please authorize the bot first using /zoho_auth")
            return

        try:
            customers = await zoho.get_customers()
            if customers:
                customer_list = "\n".join(
                    [f"{c['contact_name']}" for c in customers[:10]]
                )
                await event.reply(f"Here are the first 10 customers:\n{customer_list}")
            else:
                await event.reply("Failed to fetch customers. Please try again later.")
        except Exception as e:
            await event.reply(f"An error occurred: {str(e)}")
