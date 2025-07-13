from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Travel(Base):
    __tablename__ = "travels"
    id = Column(Integer, primary_key=True, index=True)
    province = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    tax_reduction = Column(Float, nullable=True)  # ลดหย่อนภาษี
    is_secondary = Column(Integer, default=0)     # 1 =