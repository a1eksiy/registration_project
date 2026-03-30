import pydantic



class UserCreate(pydantic.BaseModel):
    email : pydantic.EmailStr
    password : str

class UserSafe(pydantic.BaseModel):
    user_id : int 
    email : pydantic.EmailStr

    
