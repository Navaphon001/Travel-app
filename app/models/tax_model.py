from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Tax(Base):
    __tablename__ = "taxes"
    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, unique=True, index=True, nullable=False)
    reduce_tax_percent = Column(Float, nullable=False)  # เปอร์เซ็นต์ลดหย่อนภาษี
    is_secondary = Column(Integer, default=0)           # 1 = จังหวัดรอง, 0 = จังหวัดหลัก
    description = Column(String, nullable=True)         # รายละเอียดเพิ่มเติม (optional)