from sqlalchemy import Column, Integer, String
from app.database import Base

class Travel(Base):
    __tablename__ = "travels"
    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, index=True)
    description = Column(String)
    # เพิ่มฟิลด์อื่นๆตามต้องการ
