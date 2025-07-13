from pydantic import BaseModel

class TaxBase(BaseModel):
    province: str
    reduce_tax_percent: float
    is_secondary: int = 0
    description: str | None = None

class TaxCreate(TaxBase):
    pass

class TaxResponse(TaxBase):
    id: int

    class Config:
        orm_mode = True