import fastapi
from fastapi.responses import JSONResponse
import pydantic
import secrets
import redis.asyncio as redis
import app.database as db
from app.classes import UserCreate, UserSafe
app = fastapi.FastAPI()

cache = redis.Redis(host = "localhost", port=6379, decode_responses=True)




async def is_active_session(session_token : str | None) -> bool:
    if session_token:
        user_id = await cache.get(session_token)
        if user_id:
            await cache.expire(session_token, 1200, gt=True)
            return True
        
    return False


@app.get("/")
def get_root():
    return {"message": "root"}



@app.post("/login")
async def user_login(user: UserCreate, 
                     session_token: str | None = fastapi.Cookie(None)):
    is_registered = await is_active_session(session_token)
    if is_registered:
        return JSONResponse(content={"status" : "ok"},
                            status_code=200)
    user_id = await db.verify_user(user.email, user.password)

    if user_id:
        response = JSONResponse(content={"status" : "ok"})
        session_token = secrets.token_urlsafe(32)
        response.set_cookie(
        key="session_token", 
        value=session_token,
          httponly=True, 
          secure=True,
          samesite="strict",
          max_age=1200
        )
        await cache.set(session_token, user_id, ex=1200)
        return response
    else:
        return fastapi.HTTPException(status_code=400,
                                     detail="invalid user data")

    

@app.post("/logout")
async def logout(session_token: str = fastapi.Cookie(...)):
    user_session = await cache.get(session_token)
    if user_session:
        await cache.delete(session_token)
        return JSONResponse(status_code=200,
                            content="session successfully deleted")
    return fastapi.HTTPException(status_code=401, detail="invalid session token")



@app.post("/user_register")
async def user_register(user: UserCreate):
    if not await db.is_unique_email(user.email):
        raise fastapi.HTTPException(status_code=400, detail="email already exists ")
    
    add_user_successful: bool = await db.add_user(user)
    if not add_user_successful:
        raise fastapi.HTTPException(
            status_code=500, detail="error occurred when adding user to db"
        )

    response = JSONResponse(content={"status" : "ok"})
    session_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="session_token", 
        value=session_token,
          httponly=True, 
          secure=True,
          samesite="strict",
          max_age=1200
    )
    user_id = await db.get_user_id(user.email)
    if user_id:
            await cache.set(session_token, user_id, ex=1200)

    # add exception handler that rolls back changes in db
    # in case the cookie operations fail

    return response


@app.get("/get_current_user")
async def get_current_user(session_token: str = fastapi.Cookie(...)):
    user_id = await cache.get(session_token)
    if user_id:
        await cache.expire(session_token, 1200)
        user_safe = await db.get_user(user_id)
        return user_safe
    else:
        raise fastapi.HTTPException(
            status_code=401,
            detail="invalid session cookie",
        )
