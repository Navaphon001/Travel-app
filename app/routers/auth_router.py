from fastapi import APIRouter, Depends, HTTPException, status # เพิ่ม status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # <-- นำเข้า IntegrityError
from app.schemas.user_schemas import UserCreate, UserLogin, UserResponse
from app.models.user_model import User
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED) # <-- เปลี่ยนเป็น 201 Created
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # ตรวจสอบ username ซ้ำ (จากโค้ดเดิมของคุณ)
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists") # <-- ใช้ status.HTTP_400_BAD_REQUEST

    try:
        hashed_pw = hash_password(user.password)
        new_user = User(
            fullname=user.fullname,
            phone=user.phone,
            username=user.username,
            hashed_password=hashed_pw
        )
        db.add(new_user)
        db.commit() # <-- commit การเปลี่ยนแปลงลงฐานข้อมูล
        db.refresh(new_user) # <-- refresh เพื่อให้ได้ ID และข้อมูลล่าสุดจาก DB
        return new_user
    except IntegrityError: # <-- เพิ่มการจัดการ IntegrityError (เผื่อมี UNIQUE constraint อื่นๆ เช่น email, phone)
        db.rollback() # <-- สำคัญมาก: ต้อง rollback transaction หากเกิดข้อผิดพลาด
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed due to duplicate data (e.g., email or phone)." # <--- ข้อความที่อาจถูกทดสอบ
        )
    except Exception as e: # <-- จับข้อผิดพลาดอื่นๆ ทั่วไป
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during registration: {e}"
        )

@router.post("/login", status_code=status.HTTP_200_OK) # <-- กำหนด status_code เป็น 200 OK
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") # <-- ใช้ status.HTTP_401_UNAUTHORIZED
    
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}