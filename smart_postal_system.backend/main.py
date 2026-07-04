from fastapi import FastAPI
from app.routers import user_route as users
from app.database.database import Base, engine
from app.models.user_model import User

Base.metadata.create_all(bind=engine)
app = FastAPI(
title="Smart Postal System API",
version="1.0.0",
description="API for the Smart Postal System application"
)
app.include_router(users.router)

@app.get("/hello")
def home():
    return {"message": "Welcome to the Smart Postal System API!"}

@app.get("/docs")
def custom_swagger_ui_html():
    return app.openapi()