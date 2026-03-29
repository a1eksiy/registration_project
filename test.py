import database

import sqlite3
import pydantic

DB_FILENAME = "database.db"

def get_user_id(email : pydantic.EmailStr):
    with sqlite3.connect(DB_FILENAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = (?)",
                       (email,))
        id = cursor.fetchone()
        return id
    
data = database.get_user(1)
print(data)

