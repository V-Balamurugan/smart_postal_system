from fastapi import FastAPI

from app.database.database import Base, engine

# Import models so SQLAlchemy registers them
from app.models.user_model import User
from app.models.parcel_model import Parcel
from app.models.employee_model import Employee

# Import routers
from app.routers import auth_router
from app.routers import user_route
from app.routers import parcels_route
from app.routers import employee_router
from app.routers import delivery_assignment_router
from app.routers import branches_route

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Postal System API",
    version="1.0.0",
    description="API for the Smart Postal System application",
)

app.include_router(auth_router.router)
app.include_router(user_route.router)
app.include_router(parcels_route.router)
app.include_router(employee_router.router)
app.include_router(delivery_assignment_router.router)
app.include_router(branches_route.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Smart Postal System API"
    }


@app.get("/hello")
def hello():
    return {
        "message": "Welcome to the Smart Postal System API!"
    }
@app.get("/docs")
def custom_swagger_ui_html():
    return app.openapi()