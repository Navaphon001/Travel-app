from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.tax_schemas import TaxCreate, TaxResponse
from app.models.tax_model import Tax
from app.database import SessionLocal

router = APIRouter(prefix="/tax", tags=["Tax"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=TaxResponse)
def create_tax(tax: TaxCreate, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=404, detail="Tax info not found")
    return tax