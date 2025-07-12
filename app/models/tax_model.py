from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Tax(Base):
    __tablename__ = "taxes"
    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, index=True)
    reduce_tax_percent = Column(Float)
    # เพิ่มฟิลด์อื่นๆตามต้องการ
