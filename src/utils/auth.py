from functools import wraps
from config import USER_ROLES


def require_auth(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.sender_id
            user_role = USER_ROLES.get(user_id, "guest")
            if user_role in allowed_roles:
                return await func(event, *args, **kwargs)
            else:
                await event.reply("You are not authorized to use this command.")

        return wrapper

    return decorator
