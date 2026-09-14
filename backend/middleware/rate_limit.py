from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def user_key_func(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=user_key_func)
