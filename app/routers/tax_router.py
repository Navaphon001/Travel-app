from fastapi import APIRouter, Depends, HTTPException, status # เพิ่ม status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # <-- นำเข้า IntegrityError
from app.schemas.tax_schemas import TaxCreate, TaxResponse
from app.models.tax_model import Tax
from app.database import SessionLocal # หรือ get_db ถ้าคุณต้องการนำเข้า get_db โดยตรง

router = APIRouter(prefix="/tax", tags=["Tax"])

# ให้แน่ใจว่าฟังก์ชัน get_db ของคุณถูกกำหนดใน app.database.py
# และถูกนำเข้าอย่างถูกต้อง หรือถ้ามันถูกกำหนดในไฟล์เดียวกันนี้
# ก็ไม่จำเป็นต้องเปลี่ยนแปลงอะไร
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TaxResponse, status_code=status.HTTP_201_CREATED) # <-- เปลี่ยนเป็น 201 Created
def create_tax(tax: TaxCreate, db: Session = Depends(get_db)):
    # ตรวจสอบว่า province มีอยู่แล้วหรือไม่ก่อนเพิ่ม (ทางเลือก, การจับ IntegrityError ก็เพียงพอ)
    existing_tax = db.query(Tax).filter(Tax.province == tax.province).first()
    if existing_tax:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # หรือ status.HTTP_409_CONFLICT
            detail="Province already exists."
        )

    try:
        db_tax = Tax(
            province=tax.province,
            reduce_tax_percent=tax.reduce_tax_percent,
            is_secondary=tax.is_secondary,
            description=tax.description
        )
        db.add(db_tax)
        db.commit()
        db.refresh(db_tax)
        return db_tax
    except IntegrityError: # <-- จับข้อผิดพลาด UNIQUE constraint หากไม่ได้ตรวจเช็คไปก่อนหน้านี้
        db.rollback() # <--- สำคัญมาก: ต้อง rollback transaction หากเกิดข้อผิดพลาด
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # หรือ status.HTTP_409_CONFLICT
            detail="Province already exists."
        )
    except Exception as e: # <-- จับข้อผิดพลาดอื่นๆ ที่อาจเกิดขึ้น
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.get("/", response_model=list[TaxResponse])
def get_all_taxes(db: Session = Depends(get_db)):
    return db.query(Tax).all()

@router.get("/secondary/", response_model=list[TaxResponse])
def get_secondary_taxes(db: Session = Depends(get_db)):
    return db.query(Tax).filter(Tax.is_secondary == 1).all()

@router.get("/{province}", response_model=TaxResponse)
def get_tax_by_province(province: str, db: Session = Depends(get_db)):
    tax = db.query(Tax).filter(Tax.province == province).first()
    if not tax:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax info not found") # <-- ใช้ status.HTTP_404_NOT_FOUND
    return tax