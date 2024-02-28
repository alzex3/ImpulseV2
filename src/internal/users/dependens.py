from fastapi import HTTPException, Depends
from firebase_admin import auth
from firebase_admin.auth import ExpiredSessionCookieError, InvalidSessionCookieError
from starlette.requests import Request
from starlette.responses import Response

from internal.database import db
from internal.users.schema.user import User


async def get_current_user(request: Request) -> User:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")
    try:
        user = auth.verify_session_cookie(token)
        if not user.get("admin"):
            raise HTTPException(status_code=403, detail="Permission denied")
        return User(**user)
    except ExpiredSessionCookieError:
        raise HTTPException(status_code=403, detail="Token expired")
    except InvalidSessionCookieError:
        raise HTTPException(status_code=403, detail="Invalid token")


async def delete_cookie(response: Response) -> dict:
    response.set_cookie(key="session", value="", max_age=0)
    return {"message": "Session cookie cleared"}


async def cheak_coach(coach_id: str, user: Depends(get_current_user)) -> dict:
    coach = await db.get_doc("user_profile", coach_id)
    coach_dict = coach.to_dict()
    if coach_dict is None:
        raise HTTPException(status_code=404, detail="Coach not found")
