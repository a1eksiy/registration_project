import aiosqlite
import pydantic
import bcrypt
import time
from .classes import UserCreate, UserSafe

DB_FILENAME = "database.db"

async def is_unique_email(email : pydantic.EmailStr) -> bool:

    is_unique : bool = True

    async with aiosqlite.connect(DB_FILENAME) as conn:
       cursor = await conn.execute("SELECT 1 FROM users WHERE email = (?)",
                                   (email,))
       row = await cursor.fetchone()
    
    return row is None


async def add_user(user : UserCreate) -> bool:
    is_succesful : bool = True

    try:
        async with aiosqlite.connect(DB_FILENAME) as conn:
            hashed_password = bcrypt.hashpw(
                user.password.encode("utf-8"), 
                bcrypt.gensalt()
                )
            cursor =await conn.execute(
                "INSERT INTO users (email, password) VALUES (?,?)",
                (user.email, hashed_password))
            await conn.commit()
            return cursor.rowcount == 1  #only one row was affected
    except Exception as e:
        return False
    

async def get_user_id(email : pydantic.EmailStr):
    async with aiosqlite.connect(DB_FILENAME) as conn:
        
        cursor = await conn.execute("SELECT id FROM users WHERE email = (?)",
                       (email,))
        id = await cursor.fetchone()
        if id:
            return id[0]
        else:
            return None
    

async def get_user(user_id : int) -> UserSafe | None:
    async with aiosqlite.connect(DB_FILENAME) as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE id = (?)",
                       (user_id, ))
        data = await cursor.fetchone()
        if data:
            user = UserSafe(
                user_id = data[0],
                email = data[1],
            )
            return user
        else:
            return None

#return user id
async def verify_user(email : pydantic.EmailStr, password : str) -> int | None:
    async with aiosqlite.connect(DB_FILENAME) as conn:
        cursor = await conn.execute("SELECT id, email, password FROM users WHERE email = ?",
                              (email,))
        user_data = await cursor.fetchone()
        if user_data:
            hashed_password = user_data[2]
            if bcrypt.checkpw(password.encode("utf-8"), hashed_password):
                return user_data[0]
        