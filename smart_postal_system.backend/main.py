from fastapi import FastAPI
from app.routers import user_route as users
from app.database.database import Base, engine
from app.models.user_model import User
from app.routers import parcels_route
from app.routers import auth_router as auth
from app.models.parcel_model import Parcel

Base.metadata.create_all(bind=engine)
app = FastAPI(
title="Smart Postal System API",
version="1.0.0",
description="API for the Smart Postal System application"
)
app.include_router(users.router)
app.include_router(parcels_route.router)
app.include_router(auth.router)

@app.get("/hello")
def home():
    return {"message": "Welcome to the Smart Postal System API!"}

@app.get("/docs")
def custom_swagger_ui_html():
    return app.openapi()