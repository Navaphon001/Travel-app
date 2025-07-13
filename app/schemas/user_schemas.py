from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    fullname: str
    phone: str

class UserResponse(BaseModel):
    id: int
    username: str
    fullname: str
    phone: str

    class Config:
        orm_mode = True