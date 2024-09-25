from .command_handlers import register_command_handlers
from .message_handlers import register_message_handlers


def register_handlers(client, plugins):
    register_command_handlers(client, plugins)
    register_message_handlers(client, plugins)
