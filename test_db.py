from app.database import engine, Base
from app.models import travel_model, tax_model, user_model 

Base.metadata.create_all(bind=engine)
print("สร้างตาราง User เรียบร้อย")
