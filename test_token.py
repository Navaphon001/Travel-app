from app.auth import create_access_token
from datetime import timedelta

data = {"sub": "testuser"}  # จำลองผู้ใช้

# สร้าง token ที่หมดอายุใน 5 นาที
token = create_access_token(data, expires_delta=timedelta(minutes=5))

print("Generated JWT Token:")
print(token)
