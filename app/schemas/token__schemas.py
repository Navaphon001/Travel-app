from pydantic import BaseModel
from typing import Optional

# เมื่อ login สำเร็จ จะ return token แบบนี้
class Token(BaseModel):
    access_token: str
    token_type: str

# สำหรับใช้ validate token ที่ถอดรหัสแล้ว
class TokenData(BaseModel):
    username: Optional[str] = None

# ใช้รับข้อมูล login
class UserLogin(BaseModel):
    username: str
    password: str
