from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.travel_schemas import TravelCreate, TravelResponse
from app.models.travel_model import Travel
from app.database import SessionLocal

router = APIRouter(prefix="/travel", tags=["Travel"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TravelResponse)
def create_travel(travel: TravelCreate, db: Session = Depends(get_db)):
    db_travel = Travel(province=travel.province, description=travel.description)
    db.add(db_travel)
    db.commit()
    db.refresh(db_travel)
    return db_travel

@router.get("/{province}", response_model=TravelResponse)
def get_travel_by_province(province: str, db: Session = Depends(get_db)):
    travel = db.query(Travel).filter(Travel.province == province).first()
    if not travel:
        raise HTTPException(status_code=404, detail="Travel info not found")
    return travel
