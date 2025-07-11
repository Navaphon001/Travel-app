from app.database import engine, Base
from app.models import User
Base.metadata.create_all(bind=engine)
print("สร้างตาราง User เรียบร้อย")
