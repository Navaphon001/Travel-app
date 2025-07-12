from pydantic import BaseModel

class TravelBase(BaseModel):
    province: str
    description: str

class TravelCreate(TravelBase):
    pass

class TravelResponse(TravelBase):
    id: int

    class Config:
        orm_mode = True
