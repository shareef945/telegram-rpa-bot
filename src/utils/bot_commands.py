COMMANDS = {
    "help": {
        "description": "Show all available commands",
        "roles": ["guest", "user", "admin"],
    },
    "zoho_auth": {
        "description": "Authorize the bot to use Zoho Books",
        "roles": ["admin"],
    },
    "create_invoice": {
        "description": "Create a new invoice in Zoho Books",
        "roles": ["admin"],
    },
    "list_customers": {
        "description": "List customers from Zoho Books",
        "roles": ["admin"],
    },
    "gsheets_auth": {
        "description": "Authorize the bot to use Google Sheets",
        "roles": ["admin"],
    },
    "list_workbooks": {
        "description": "List available Google Sheets workbooks",
        "roles": ["admin"],
    },
    "select_workbook": {
        "description": "Select a Google Sheets workbook",
        "roles": ["admin"],
    },
    "select_worksheet": {
        "description": "Select a worksheet from the chosen workbook",
        "roles": ["admin"],
    },
    "add_row": {
        "description": "Add a new row to the selected worksheet",
        "roles": ["admin"],
    },
}


def get_commands_description(user_role="guest"):
    return "\n".join(
        [
            f"/{cmd} - {info['description']}"
            for cmd, info in COMMANDS.items()
            if user_role in info["roles"]
        ]
    )
