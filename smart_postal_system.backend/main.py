from fastapi import FastAPI

app = FastAPI(
title="Smart Postal System API",
version="1.0.0",
description="API for the Smart Postal System application"
)

@app.get("/")
def home():
    return {"message": "Welcome to the Smart Postal System API!"}

@app.get("/docs")
def custom_swagger_ui_html():
    return app.openapi()