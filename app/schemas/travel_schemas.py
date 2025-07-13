from pydantic import BaseModel

class TravelBase(BaseModel):
    province: str
    description: str
    tax_reduction: float = 0.0
    is_secondary: int = 0

class TravelCreate(TravelBase):
    pass

class TravelResponse(TravelBase):
    id: int

    class Config:
        orm_mode = True