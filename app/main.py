from fastapi import FastAPI
from app.routers import register_router

app = FastAPI()

app.include_router(register_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Travel Tax API"}
