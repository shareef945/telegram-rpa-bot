COMMANDS = {
    "start": {
        "description": "Start the bot and see an overview of its capabilities",
        "roles": ["guest", "user", "admin"],
    },
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
    "my_role": {
        "description": "Show your current role",
        "roles": ["guest", "user", "admin"],
    },
    # Add more commands for your custom APIs and other functionalities
}


def get_commands_description(user_role="guest"):
    return "\n".join(
        [
            f"/{cmd} - {info['description']}"
            for cmd, info in COMMANDS.items()
            if user_role in info["roles"]
        ]
    )
