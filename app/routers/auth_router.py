from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user_schemas import UserCreate, UserLogin, UserResponse
from app.models.user_model import User
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # ตรวจสอบ username ซ้ำ
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = hash_password(user.password)
    new_user = User(
        fullname=user.fullname,
        phone=user.phone,
        username=user.username,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
