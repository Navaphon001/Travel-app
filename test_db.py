from app.database import engine, Base

print("สร้างฐานข้อมูล SQLite...")
Base.metadata.create_all(bind=engine)
print("สำเร็จ")
