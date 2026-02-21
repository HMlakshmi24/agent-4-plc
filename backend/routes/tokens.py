from fastapi import APIRouter, Request, HTTPException
from backend.token_manager import get_token_usage, TOKEN_LIMIT

router = APIRouter(prefix="/api/tokens", tags=["tokens"])

async def get_email_from_req(request: Request):
    # Try custom header first for mock cached users
    email = request.headers.get("X-User-Email")
    if email:
        return email
    try:
        from backend.utils import get_current_user
        user = await get_current_user(request)
        return user["email"]
    except:
        return None

@router.get("/")
async def get_tokens(request: Request):
    email = await get_email_from_req(request)
    if not email:
        return {"used": 0, "limit": TOKEN_LIMIT, "blocked": False}

    usage = get_token_usage(email)
    if not usage:
        return {"used": 0, "limit": TOKEN_LIMIT, "blocked": False}

    return {
        "used": usage["tokens_used"],
        "limit": TOKEN_LIMIT,
        "blocked": usage["is_blocked"]
    }
